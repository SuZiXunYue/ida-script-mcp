# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
