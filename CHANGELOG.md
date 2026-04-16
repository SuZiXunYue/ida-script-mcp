# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
