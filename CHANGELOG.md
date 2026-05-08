# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-05-08

### Added
- **Async task execution system**: Long-running scripts no longer cause client disconnection. Scripts are submitted asynchronously to IDA, and the MCP server polls for completion with exponential backoff (0.5s → 5s cap). If the configurable timeout (default: 600s) is exceeded, a `task_id` is returned for later status queries.
- **`check_task_status` tool**: New MCP tool to query the status and result of a long-running script execution task by its `task_id`.
- **`timeout` parameter for `execute_idapython`**: Configurable maximum wait time (default: 600 seconds) before returning a `task_id` for deferred polling.
- **Task management endpoints in IDA plugin**: `GET /task/{id}` to query task status/result, `GET /tasks` to list all tasks.
- **`async` mode for `POST /execute`**: IDA plugin now accepts `{"async": true}` to submit scripts for background execution and immediately return a `task_id`.
- **ThreadingMixIn HTTP server**: The IDA plugin HTTP server now handles each request in a separate thread, preventing a single long-running script from blocking other requests (e.g., health checks, task status queries).

### Fixed
- **Client disconnection on long-running scripts**: Previously, scripts running longer than 60 seconds would cause the MCP server's HTTP connection to IDA to time out, while the script continued running in IDA with no way to retrieve the result. The new async task system eliminates this issue.
- **HTTP server blocking**: The IDA plugin's single-threaded HTTP server could be blocked by a running script, making all other endpoints (health, metadata) unreachable. Switched to `ThreadingMixIn` for concurrent request handling.

## [1.1.0] - 2026-04-16

### Fixed
- **Windows multi-instance port collision**: On Windows, all IDA instances would bind to the same port (13338) because `SO_REUSEADDR` allows multiple processes to bind the same port without error. This caused all MCP requests to route to a single instance regardless of `instance_id`. Fixed by:
  - Setting `allow_reuse_address = False` on Windows to prevent silent port sharing
  - Adding pre-bind port detection (`_is_port_in_use()`) so occupied ports are skipped before attempting to bind
  - Retaining `allow_reuse_address = True` on Linux/macOS where `SO_REUSEADDR` only reuses TIME_WAIT ports

## [1.0.0] - 2024-01-15

### Added
- Initial release
- MCP server for executing IDAPython scripts in IDA Pro
- Support for multiple IDA instances simultaneously
- Auto-discovery of running IDA instances
- Execute Python code or script files in IDA context
- Full access to all IDA API modules (idaapi, idc, idautils, etc.)
- Capture stdout/stderr output
- Jupyter-style expression return values
- Connection health monitoring
- IDA Pro plugin installer
- Cross-platform support (Windows, macOS, Linux)

### Tools Provided
- `list_ida_instances`: List all running IDA instances
- `execute_idapython`: Execute Python code in IDA context
- `check_ida_connection`: Check connection status to IDA instances
- `get_ida_database_info`: Get information about IDA database

### Security
- Plugin binds to localhost (127.0.0.1) by default
- No external network exposure

[1.0.0]: https://github.com/yourusername/ida-script-mcp/releases/tag/v1.0.0
