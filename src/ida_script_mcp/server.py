"""IDA Script MCP Server.

This is the MCP server that provides tools for AI to execute IDAPython scripts
in IDA Pro. It communicates with the IDA Pro plugin via HTTP.

Supports multiple IDA instances running simultaneously.
"""

import os
import argparse
import json
import http.client
from typing import Optional, List
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("ida_script_mcp")

INSTANCE_INFO_FILE = Path.home() / ".ida_script_mcp_instances.json"


def get_ida_host() -> str:
    """Get IDA plugin host from environment or default."""
    return os.environ.get("IDA_SCRIPT_MCP_HOST", "127.0.0.1")


def get_ida_port() -> Optional[int]:
    """Get IDA plugin port from environment."""
    port = os.environ.get("IDA_SCRIPT_MCP_PORT")
    return int(port) if port else None


def get_ida_instance_id() -> Optional[str]:
    """Get IDA instance ID from environment."""
    return os.environ.get("IDA_SCRIPT_MCP_INSTANCE_ID")


class ExecuteScriptInput(BaseModel):
    """Input model for script execution."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    code: Optional[str] = Field(
        default=None,
        description="Python code string to execute in IDA context. Either 'code' or 'script_path' must be provided.",
    )
    script_path: Optional[str] = Field(
        default=None,
        description="Path to a Python script file to execute in IDA context. Either 'code' or 'script_path' must be provided.",
    )
    capture_output: bool = Field(
        default=True,
        description="Whether to capture stdout/stderr output (default: True).",
    )
    instance_id: Optional[str] = Field(
        default=None,
        description="Target IDA instance ID (optional, uses default if not specified).",
    )
    port: Optional[int] = Field(
        default=None,
        description="Target IDA instance port (optional, uses default if not specified).",
    )


def is_process_alive(pid: int) -> bool:
    """Check if a process with given PID is alive (cross-platform)."""
    import sys
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                try:
                    exit_code = ctypes.c_ulong()
                    if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                        return exit_code.value == STILL_ACTIVE
                finally:
                    kernel32.CloseHandle(handle)
        except Exception:
            pass
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def list_instances() -> dict:
    """List all registered IDA instances."""
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
        if pid and is_process_alive(pid):
            alive_instances[iid] = info
    
    return alive_instances


def find_instance_port(instance_id: Optional[str] = None) -> tuple[Optional[int], str]:
    """Find the port for an IDA instance.
    
    Returns:
        tuple: (port, instance_id) or (None, error_message)
    """
    env_port = get_ida_port()
    env_instance_id = get_ida_instance_id() or instance_id
    
    if env_port:
        return env_port, f"port:{env_port}"
    
    instances = list_instances()
    
    if not instances:
        return None, "No IDA instances found. Start IDA Pro and enable the plugin."
    
    if env_instance_id:
        if env_instance_id in instances:
            info = instances[env_instance_id]
            return info.get("port"), env_instance_id
        for iid, info in instances.items():
            if env_instance_id in iid or (info.get("database") and env_instance_id in info.get("database", "")):
                return info.get("port"), iid
        return None, f"Instance '{env_instance_id}' not found"
    
    if len(instances) == 1:
        iid, info = next(iter(instances.items()))
        return info.get("port"), iid
    
    instance_list = [
        f"  - {iid}: {info.get('database', 'unknown')} (port {info.get('port')})"
        for iid, info in instances.items()
    ]
    return None, f"Multiple IDA instances found:\n" + "\n".join(instance_list) + "\n\nSpecify instance_id or port."


def make_ida_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[dict] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    timeout: float = 60.0,
) -> dict:
    """Make an HTTP request to the IDA plugin."""
    host = host or get_ida_host()
    if port is None:
        port, _ = find_instance_port()
        if port is None:
            raise RuntimeError("Could not find IDA instance")
    
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        headers = {"Content-Type": "application/json"}
        body = json.dumps(data) if data else None
        
        conn.request(method, endpoint, body, headers)
        response = conn.getresponse()
        raw_data = response.read().decode("utf-8")
        
        if response.status >= 400:
            raise RuntimeError(f"HTTP {response.status}: {raw_data}")
        
        return json.loads(raw_data)
    except Exception as e:
        raise RuntimeError(f"Failed to connect to IDA plugin at {host}:{port}: {e}")
    finally:
        conn.close()


@mcp.tool(
    name="list_ida_instances",
    annotations={
        "title": "List IDA Instances",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def list_ida_instances() -> str:
    """List all running IDA instances with MCP plugin enabled.
    
    Returns:
        str: JSON-formatted list of IDA instances with their ports and database info.
        
    Example response:
        {
          "count": 2,
          "instances": {
            "12345_crackme.exe": {"port": 13338, "database": "crackme.exe"},
            "67890_malware.dll": {"port": 13339, "database": "malware.dll"}
          }
        }
    """
    instances = list_instances()
    
    if not instances:
        return json.dumps({
            "count": 0,
            "instances": {},
            "hint": "No IDA instances found. Start IDA Pro and enable the IDA-Script-MCP plugin.",
        }, indent=2, ensure_ascii=False)
    
    return json.dumps({
        "count": len(instances),
        "instances": instances,
    }, indent=2, ensure_ascii=False)


@mcp.tool(
    name="execute_idapython",
    annotations={
        "title": "Execute IDAPython Script",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def execute_idapython(params: ExecuteScriptInput) -> str:
    """Execute Python code or script file in IDA Pro context.
    
    This tool sends Python code to the IDA Pro plugin for execution.
    The code runs in IDA's main thread with full access to all IDA API modules.
    
    Args:
        params (ExecuteScriptInput): Validated input parameters containing:
            - code (Optional[str]): Python code string to execute
            - script_path (Optional[str]): Path to Python script file
            - capture_output (bool): Whether to capture stdout/stderr
            - instance_id (Optional[str]): Target IDA instance ID (e.g., "crackme.exe" or full ID)
            - port (Optional[int]): Target IDA instance port (e.g., 13338)
            
    Returns:
        str: JSON-formatted string containing:
            - result: The return value of the last expression
            - stdout: Captured standard output
            - stderr: Captured standard output (including errors)
            - instance: The IDA instance that executed the code
            
    Examples:
        # Execute on default instance
        execute_idapython(code="print(idaapi.get_root_filename())")
        
        # Execute on specific instance by database name
        execute_idapython(code="len(list(idautils.Functions()))", instance_id="crackme.exe")
        
        # Execute on specific instance by port
        execute_idapython(code="idc.get_func_name(0x401000)", port=13339)
    """
    if params.code is None and params.script_path is None:
        return json.dumps({
            "result": None,
            "stdout": "",
            "stderr": "Error: Either 'code' or 'script_path' must be provided",
        }, indent=2)
    
    if params.port:
        port = params.port
        instance_info = f"port:{port}"
    else:
        port, instance_info = find_instance_port(params.instance_id)
    
    if port is None:
        return json.dumps({
            "result": "",
            "stdout": "",
            "stderr": f"Error: {instance_info}",
        }, indent=2)
    
    try:
        result = make_ida_request(
            "/execute",
            method="POST",
            data={
                "code": params.code,
                "script_path": params.script_path,
                "capture_output": params.capture_output,
            },
            port=port,
        )
        result["instance"] = instance_info
        result["port"] = port
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "result": "",
            "stdout": "",
            "stderr": f"Error: {e}\n\nMake sure IDA Pro is running with the IDA-Script-MCP plugin started.\n"
                      f"Use Edit -> Plugins -> IDA-Script-MCP (Ctrl+Alt+S) to start the server.",
        }, indent=2)


@mcp.tool(
    name="check_ida_connection",
    annotations={
        "title": "Check IDA Pro Connection",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def check_ida_connection() -> str:
    """Check if IDA Pro instances are running and accessible.
    
    Returns:
        str: JSON-formatted string with connection status and all instances.
    """
    instances = list_instances()
    
    if not instances:
        return json.dumps({
            "connected": False,
            "count": 0,
            "instances": {},
            "hint": "No IDA instances found. Start IDA Pro and enable the IDA-Script-MCP plugin.",
        }, indent=2, ensure_ascii=False)
    
    results = {}
    for iid, info in instances.items():
        port = info.get("port")
        try:
            health = make_ida_request("/health", port=port, timeout=2.0)
            metadata = make_ida_request("/metadata", port=port, timeout=2.0)
            results[iid] = {
                "connected": True,
                "health": health,
                "metadata": metadata,
            }
        except Exception as e:
            results[iid] = {
                "connected": False,
                "error": str(e),
            }
    
    return json.dumps({
        "connected": True,
        "count": len(instances),
        "instances": results,
    }, indent=2, ensure_ascii=False)


@mcp.tool(
    name="get_ida_database_info",
    annotations={
        "title": "Get IDA Database Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def get_ida_database_info(instance_id: Optional[str] = None) -> str:
    """Get information about an IDA database.
    
    Args:
        instance_id: Target IDA instance ID (optional, uses default if not specified).
        
    Returns:
        str: JSON-formatted string with database information.
    """
    port, instance_info = find_instance_port(instance_id)
    
    if port is None:
        return json.dumps({
            "error": instance_info,
        }, indent=2)
    
    try:
        result = make_ida_request("/metadata", port=port)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "hint": "Make sure IDA Pro is running with the IDA-Script-MCP plugin started.",
        }, indent=2)


def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="IDA Script MCP Server")
    parser.add_argument(
        "--ida-host",
        type=str,
        default=None,
        help="IDA plugin host (default: 127.0.0.1, env: IDA_SCRIPT_MCP_HOST)",
    )
    parser.add_argument(
        "--ida-port",
        type=int,
        default=None,
        help="IDA plugin port (default: auto-detect, env: IDA_SCRIPT_MCP_PORT)",
    )
    parser.add_argument(
        "--ida-instance",
        type=str,
        default=None,
        help="IDA instance ID to connect to (env: IDA_SCRIPT_MCP_INSTANCE_ID)",
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "http"],
        help="MCP transport: 'stdio' (default) or 'http'",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for HTTP transport (default: 8765)",
    )
    args = parser.parse_args()
    
    if args.ida_host:
        os.environ["IDA_SCRIPT_MCP_HOST"] = args.ida_host
    if args.ida_port:
        os.environ["IDA_SCRIPT_MCP_PORT"] = str(args.ida_port)
    if args.ida_instance:
        os.environ["IDA_SCRIPT_MCP_INSTANCE_ID"] = args.ida_instance
    
    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport="sse", port=args.port)


if __name__ == "__main__":
    main()
