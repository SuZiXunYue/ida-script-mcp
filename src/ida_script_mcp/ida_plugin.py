"""IDA Pro Plugin for IDA Script MCP.

This plugin runs inside IDA Pro and provides an HTTP server for executing
IDAPython scripts received from MCP clients.

Supports multiple IDA instances running simultaneously.
"""

import json
import io
import sys
import ast
import socket
import traceback
import queue
import os
import time
import uuid
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Any, Optional
from urllib.parse import urlparse
from pathlib import Path

try:
    import idaapi
    import ida_kernwin
    import idc
    HAS_IDA = True
except ImportError:
    HAS_IDA = False

PLUGIN_NAME = "IDA-Script-MCP"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 13338
MAX_PORT_RANGE = 100

INSTANCE_INFO_FILE = Path.home() / ".ida_script_mcp_instances.json"
INSTANCE_LOCK = threading.Lock()


def get_instance_id() -> str:
    """Get unique instance ID for this IDA process."""
    if HAS_IDA:
        try:
            db_path = idaapi.get_input_file_path()
            if db_path:
                db_name = os.path.basename(db_path)
                return f"{os.getpid()}_{db_name}"
        except:
            pass
    return str(os.getpid())


class InstanceRegistry:
    """Registry for tracking multiple IDA instances."""
    
    def __init__(self):
        self.instance_id = get_instance_id()
        self.port: Optional[int] = None
        self.host = DEFAULT_HOST
        self.database: Optional[str] = None
    
    def _load_instances(self) -> dict:
        """Load instances from file."""
        try:
            if INSTANCE_INFO_FILE.exists():
                with open(INSTANCE_INFO_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_instances(self, instances: dict):
        """Save instances to file."""
        try:
            with open(INSTANCE_INFO_FILE, 'w', encoding='utf-8') as f:
                json.dump(instances, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[{PLUGIN_NAME}] Warning: Failed to save instance info: {e}")
    
    def _get_database_info(self) -> dict:
        """Get current database info."""
        if HAS_IDA:
            try:
                return {
                    "database": idaapi.get_root_filename(),
                    "database_path": idaapi.get_input_file_path(),
                    "platform": sys.platform,
                }
            except:
                pass
        return {"database": None, "database_path": None, "platform": sys.platform}
    
    def register(self, port: int):
        """Register this instance."""
        self.port = port
        db_info = self._get_database_info()
        self.database = db_info.get("database")
        
        with INSTANCE_LOCK:
            instances = self._load_instances()
            instances[self.instance_id] = {
                "pid": os.getpid(),
                "port": port,
                "host": self.host,
                **db_info,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._save_instances(instances)
            print(f"[{PLUGIN_NAME}] Registered instance: {self.instance_id}")
    
    def unregister(self):
        """Unregister this instance."""
        with INSTANCE_LOCK:
            instances = self._load_instances()
            if self.instance_id in instances:
                del instances[self.instance_id]
                self._save_instances(instances)
                print(f"[{PLUGIN_NAME}] Unregistered instance: {self.instance_id}")
    
    @staticmethod
    def list_instances() -> dict:
        """List all registered instances (static method for server use)."""
        with INSTANCE_LOCK:
            try:
                if INSTANCE_INFO_FILE.exists():
                    with open(INSTANCE_INFO_FILE, 'r', encoding='utf-8') as f:
                        instances = json.load(f)
                else:
                    return {}
            except Exception:
                return {}
            
            alive_instances = {}
            for iid, info in instances.items():
                pid = info.get("pid")
                if pid:
                    try:
                        os.kill(pid, 0)
                        alive_instances[iid] = info
                    except (OSError, ProcessLookupError):
                        pass
            
            if len(alive_instances) != len(instances):
                try:
                    with open(INSTANCE_INFO_FILE, 'w', encoding='utf-8') as f:
                        json.dump(alive_instances, f, indent=2, ensure_ascii=False)
                except:
                    pass
            
            return alive_instances


instance_registry = InstanceRegistry()


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    def __init__(self, task_id, code=None, script_path=None, capture_output=True):
        self.task_id = task_id
        self.code = code
        self.script_path = script_path
        self.capture_output = capture_output
        self.status = TaskStatus.PENDING
        self.result = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None

    def to_dict(self, include_result=False):
        d = {
            "task_id": self.task_id,
            "status": self.status,
            "created_at": self.created_at,
        }
        if self.started_at is not None:
            d["started_at"] = self.started_at
        if self.completed_at is not None:
            d["completed_at"] = self.completed_at
            d["duration"] = round(
                self.completed_at - (self.started_at or self.created_at), 3
            )
        if include_result and self.result is not None:
            d.update(self.result)
        return d


class TaskManager:
    MAX_TASKS = 100

    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.lock = threading.Lock()

    def create_task(self, code=None, script_path=None, capture_output=True):
        task_id = uuid.uuid4().hex[:8]
        task = Task(task_id, code, script_path, capture_output)
        with self.lock:
            if len(self.tasks) >= self.MAX_TASKS:
                self._cleanup()
            self.tasks[task_id] = task
        return task

    def get_task(self, task_id: str):
        with self.lock:
            return self.tasks.get(task_id)

    def list_tasks(self):
        with self.lock:
            return [t.to_dict() for t in self.tasks.values()]

    def _cleanup(self):
        completed = [
            (tid, t)
            for tid, t in self.tasks.items()
            if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        ]
        completed.sort(key=lambda x: x[1].completed_at or 0)
        for tid, _ in completed[: len(completed) // 2 + 1]:
            del self.tasks[tid]


task_manager = TaskManager()


def execute_on_main_thread(func, *args, **kwargs):
    """Execute a function on IDA's main thread and return the result."""
    if not HAS_IDA:
        return func(*args, **kwargs)
    
    result_queue = queue.Queue()
    
    def wrapper():
        try:
            result = func(*args, **kwargs)
            result_queue.put(("success", result))
        except Exception as e:
            result_queue.put(("error", str(e), traceback.format_exc()))
    
    idaapi.execute_sync(wrapper, idaapi.MFF_WRITE)
    result = result_queue.get()
    
    if result[0] == "error":
        raise Exception(f"{result[1]}\n{result[2]}")
    return result[1]


def execute_python_script(
    code: Optional[str] = None,
    script_path: Optional[str] = None,
    capture_output: bool = True,
) -> dict:
    """Execute Python code or script file in IDA context."""
    if code is None and script_path is None:
        return {
            "result": None,
            "stdout": "",
            "stderr": "Error: Either 'code' or 'script_path' must be provided",
        }
    
    if script_path:
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return {
                "result": None,
                "stdout": "",
                "stderr": f"Error reading script file: {e}",
            }
    
    stdout_capture = io.StringIO() if capture_output else None
    stderr_capture = io.StringIO() if capture_output else None
    old_stdout = sys.stdout if capture_output else None
    old_stderr = sys.stderr if capture_output else None
    
    try:
        if capture_output:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
        
        exec_globals = _build_ida_globals()
        exec_locals = {}
        result_value = None
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            exec(code, exec_globals, exec_locals)
            exec_globals.update(exec_locals)
            if "result" in exec_locals:
                result_value = str(exec_locals["result"])
            elif exec_locals:
                last_key = list(exec_locals.keys())[-1]
                result_value = str(exec_locals[last_key])
        else:
            if not tree.body:
                pass
            elif len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
                result_value = str(eval(code, exec_globals))
            elif isinstance(tree.body[-1], ast.Expr):
                if len(tree.body) > 1:
                    exec_tree = ast.Module(body=tree.body[:-1], type_ignores=[])
                    exec(
                        compile(exec_tree, "<string>", "exec"),
                        exec_globals,
                        exec_locals,
                    )
                    exec_globals.update(exec_locals)
                eval_tree = ast.Expression(body=tree.body[-1].value)
                result_value = str(
                    eval(compile(eval_tree, "<string>", "eval"), exec_globals)
                )
            else:
                exec(code, exec_globals, exec_locals)
                exec_globals.update(exec_locals)
                if "result" in exec_locals:
                    result_value = str(exec_locals["result"])
                elif exec_locals:
                    last_key = list(exec_locals.keys())[-1]
                    result_value = str(exec_locals[last_key])
        
        stdout_text = stdout_capture.getvalue() if stdout_capture else ""
        stderr_text = stderr_capture.getvalue() if stderr_capture else ""
        
        return {
            "result": result_value or "",
            "stdout": stdout_text,
            "stderr": stderr_text,
        }
    
    except Exception:
        return {
            "result": "",
            "stdout": stdout_capture.getvalue() if stdout_capture else "",
            "stderr": traceback.format_exc(),
        }
    finally:
        if capture_output:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


def _build_ida_globals() -> dict:
    """Build the global namespace for script execution with IDA modules."""
    def lazy_import(module_name: str):
        try:
            return __import__(module_name)
        except Exception:
            return None
    
    if not HAS_IDA:
        return {"__builtins__": __builtins__}
    
    return {
        "__builtins__": __builtins__,
        "idaapi": idaapi,
        "idc": idc,
        "idautils": lazy_import("idautils"),
        "ida_allins": lazy_import("ida_allins"),
        "ida_auto": lazy_import("ida_auto"),
        "ida_bitrange": lazy_import("ida_bitrange"),
        "ida_bytes": lazy_import("ida_bytes"),
        "ida_dbg": lazy_import("ida_dbg"),
        "ida_dirtree": lazy_import("ida_dirtree"),
        "ida_diskio": lazy_import("ida_diskio"),
        "ida_entry": lazy_import("ida_entry"),
        "ida_expr": lazy_import("ida_expr"),
        "ida_fixup": lazy_import("ida_fixup"),
        "ida_fpro": lazy_import("ida_fpro"),
        "ida_frame": lazy_import("ida_frame"),
        "ida_funcs": lazy_import("ida_funcs"),
        "ida_gdl": lazy_import("ida_gdl"),
        "ida_graph": lazy_import("ida_graph"),
        "ida_hexrays": lazy_import("ida_hexrays"),
        "ida_ida": lazy_import("ida_ida"),
        "ida_idd": lazy_import("ida_idd"),
        "ida_idp": lazy_import("ida_idp"),
        "ida_ieee": lazy_import("ida_ieee"),
        "ida_kernwin": ida_kernwin,
        "ida_libfuncs": lazy_import("ida_libfuncs"),
        "ida_lines": lazy_import("ida_lines"),
        "ida_loader": lazy_import("ida_loader"),
        "ida_merge": lazy_import("ida_merge"),
        "ida_mergemod": lazy_import("ida_mergemod"),
        "ida_moves": lazy_import("ida_moves"),
        "ida_nalt": lazy_import("ida_nalt"),
        "ida_name": lazy_import("ida_name"),
        "ida_netnode": lazy_import("ida_netnode"),
        "ida_offset": lazy_import("ida_offset"),
        "ida_pro": lazy_import("ida_pro"),
        "ida_problems": lazy_import("ida_problems"),
        "ida_range": lazy_import("ida_range"),
        "ida_regfinder": lazy_import("ida_regfinder"),
        "ida_registry": lazy_import("ida_registry"),
        "ida_search": lazy_import("ida_search"),
        "ida_segment": lazy_import("ida_segment"),
        "ida_segregs": lazy_import("ida_segregs"),
        "ida_srclang": lazy_import("ida_srclang"),
        "ida_strlist": lazy_import("ida_strlist"),
        "ida_struct": lazy_import("ida_struct"),
        "ida_tryblks": lazy_import("ida_tryblks"),
        "ida_typeinf": lazy_import("ida_typeinf"),
        "ida_ua": lazy_import("ida_ua"),
        "ida_undo": lazy_import("ida_undo"),
        "ida_xref": lazy_import("ida_xref"),
        "ida_enum": lazy_import("ida_enum"),
    }


class IdaScriptHttpHandler(BaseHTTPRequestHandler):
    """HTTP request handler for IDA Script MCP."""
    
    server: "IdaScriptHttpServer"
    
    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        pass
    
    def _send_json_response(self, status: int, data: dict):
        """Send a JSON response."""
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json_response(200, {
                "status": "ok",
                "plugin": PLUGIN_NAME,
                "instance_id": instance_registry.instance_id,
                "port": instance_registry.port,
            })
        elif parsed.path == "/metadata":
            db_info = instance_registry._get_database_info()
            self._send_json_response(200, {
                "instance_id": instance_registry.instance_id,
                "port": instance_registry.port,
                **db_info,
            })
        elif parsed.path == "/tasks":
            self._send_json_response(200, {"tasks": task_manager.list_tasks()})
        elif parsed.path.startswith("/task/"):
            task_id = parsed.path[len("/task/"):]
            task = task_manager.get_task(task_id)
            if task:
                self._send_json_response(200, task.to_dict(include_result=True))
            else:
                self._send_json_response(404, {"error": f"Task '{task_id}' not found"})
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)

        if parsed.path != "/execute":
            self._send_json_response(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            request_data = json.loads(body)
        except json.JSONDecodeError as e:
            self._send_json_response(400, {"error": f"Invalid JSON: {e}"})
            return

        code = request_data.get("code")
        script_path = request_data.get("script_path")
        capture_output = request_data.get("capture_output", True)
        async_mode = request_data.get("async", False)

        if async_mode:
            task = task_manager.create_task(code, script_path, capture_output)

            def run_task():
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                try:
                    if HAS_IDA:
                        result = execute_on_main_thread(
                            execute_python_script,
                            code=task.code,
                            script_path=task.script_path,
                            capture_output=task.capture_output,
                        )
                    else:
                        result = execute_python_script(
                            code=task.code,
                            script_path=task.script_path,
                            capture_output=task.capture_output,
                        )
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.result = {
                        "result": "",
                        "stdout": "",
                        "stderr": f"Execution error: {e}",
                    }
                finally:
                    task.completed_at = time.time()

            thread = threading.Thread(target=run_task, daemon=True)
            thread.start()
            self._send_json_response(200, task.to_dict())
        else:
            try:
                if HAS_IDA:
                    result = execute_on_main_thread(
                        execute_python_script,
                        code=code,
                        script_path=script_path,
                        capture_output=capture_output,
                    )
                else:
                    result = execute_python_script(
                        code=code,
                        script_path=script_path,
                        capture_output=capture_output,
                    )
                self._send_json_response(200, result)
            except Exception as e:
                self._send_json_response(500, {
                    "result": "",
                    "stdout": "",
                    "stderr": f"Execution error: {e}",
                })


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Thread-per-request HTTP server for IDA Script MCP."""
    daemon_threads = True
    allow_reuse_address = sys.platform != "win32"


class IdaScriptHttpServer(ThreadingHTTPServer):
    """HTTP server for IDA Script MCP."""

    def __init__(self, host: str, port: int):
        super().__init__((host, port), IdaScriptHttpHandler)
        self.host = host
        self.port = port


if HAS_IDA:
    class IDAScriptMCPPlugin(idaapi.plugin_t):
        """IDA Pro plugin for IDA Script MCP."""
        
        flags = idaapi.PLUGIN_KEEP
        comment = "IDA Script MCP Plugin"
        help = "IDA Script MCP - Execute Python scripts via MCP"
        wanted_name = PLUGIN_NAME
        wanted_hotkey = "Ctrl-Alt-S"
        
        def init(self):
            print(f"[{PLUGIN_NAME}] Plugin loaded (supports multiple instances)")
            self.server: Optional[IdaScriptHttpServer] = None
            self.host = DEFAULT_HOST
            self.port = DEFAULT_PORT
            self.server_thread: Optional[threading.Thread] = None
            return idaapi.PLUGIN_KEEP
        
        def run(self, arg):
            if self.server:
                self._stop_server()
                return
            
            self._start_server()
        
        def _is_port_in_use(self, port: int) -> bool:
            """Check if a port is already in use by trying to connect to it."""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                try:
                    s.connect((self.host, port))
                    return True
                except (ConnectionRefusedError, socket.timeout, OSError):
                    return False

        def _start_server(self):
            """Start the HTTP server."""
            port = self.port
            max_port = port + MAX_PORT_RANGE

            while port < max_port:
                if self._is_port_in_use(port):
                    print(f"[{PLUGIN_NAME}] Port {port} is already in use, trying next...")
                    port += 1
                    continue
                try:
                    self.server = IdaScriptHttpServer(self.host, port)
                    self.port = port

                    instance_registry.register(port)

                    self.server_thread = threading.Thread(
                        target=self.server.serve_forever,
                        daemon=True
                    )
                    self.server_thread.start()

                    print(f"[{PLUGIN_NAME}] Server started at http://{self.host}:{port}")
                    print(f"[{PLUGIN_NAME}] Instance ID: {instance_registry.instance_id}")
                    print(f"[{PLUGIN_NAME}] Database: {instance_registry.database}")
                    print(f"[{PLUGIN_NAME}] Execute endpoint: POST http://{self.host}:{port}/execute")
                    return
                except OSError as e:
                    if e.errno in (48, 98, 10048):
                        port += 1
                    else:
                        raise

            print(f"[{PLUGIN_NAME}] Error: No available port in range {self.port}-{max_port - 1}")
        
        def _stop_server(self):
            """Stop the HTTP server."""
            if self.server:
                instance_registry.unregister()
                self.server.shutdown()
                self.server = None
                self.server_thread = None
                print(f"[{PLUGIN_NAME}] Server stopped")
        
        def term(self):
            self._stop_server()


    def PLUGIN_ENTRY():
        """Plugin entry point for IDA Pro."""
        return IDAScriptMCPPlugin()
