# IDA Script MCP

A Model Context Protocol (MCP) server for executing IDAPython scripts in IDA Pro. This enables AI assistants like Claude to run Python code directly in IDA Pro's context.

## Features

- Execute Python code or script files in IDA Pro context
- Full access to all IDA API modules (idaapi, idc, idautils, etc.)
- Capture stdout/stderr output
- Return values from expressions
- Connection health monitoring
- **Support for multiple IDA instances simultaneously**

## Architecture

### Single Instance
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Assistant  │────▶│   MCP Server    │────▶│   IDA Plugin    │
│   (Claude, etc) │     │ (FastMCP/stdio) │     │ (HTTP Server)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                      │
                                                      ▼
                                                ┌─────────────────┐
                                                │    IDA Pro      │
                                                │  (Main Thread)  │
                                                └─────────────────┘
```

### Multiple Instances
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Assistant  │────▶│   MCP Server    │────▶│ IDA Instance 1  │
│   (Claude, etc) │     │ (Auto-discover) │     │  :13338 crackme │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              │                  ┌─────────────────┐
                              └─────────────────▶│ IDA Instance 2  │
                                                 │  :13339 malware │
                                                 └─────────────────┘
```

## Requirements

- **IDA Pro 8.3+** (IDA Free not supported)
- **Python 3.11+**
- OS: Windows / macOS / Linux

---

## Installation

### Method 1: Using Install Command (Recommended)

After installing the Python package, use the `ida-script-mcp-install` command:

```bash
# 1. Install Python package
pip install ida-script-mcp

# 2. Install IDA plugin
ida-script-mcp-install install

# 3. Configure MCP clients (optional)
ida-script-mcp-install install claude      # Configure Claude Desktop
ida-script-mcp-install install claude,cursor  # Multiple clients

# List available clients
ida-script-mcp-install --list-clients
```

### Method 2: From Source

```bash
git clone https://github.com/yourusername/ida-script-mcp.git
cd ida-script-mcp

pip install -e .
ida-script-mcp-install install
```

### Method 3: Manual Installation

```bash
# Copy plugin to IDA user directory
# Windows: %APPDATA%\Hex-Rays\IDA Pro\plugins\
# macOS/Linux: ~/.idapro/plugins/

cp src/ida_script_mcp/ida_plugin.py ~/.idapro/plugins/ida_script_mcp.py
```

---

## Install Command Reference

```bash
# Install IDA plugin only
ida-script-mcp-install install

# Install plugin and configure MCP client
ida-script-mcp-install install claude
ida-script-mcp-install install claude,cursor,vscode

# Use project-level config
ida-script-mcp-install install --project claude

# Uninstall
ida-script-mcp-install uninstall

# List available MCP clients
ida-script-mcp-install --list-clients

# Show MCP config snippet
ida-script-mcp-install --config
```

### Supported MCP Clients

| Client | Config File |
|--------|-------------|
| Claude | `claude_desktop_config.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.claude.json` |
| VS Code | `settings.json` |
| Windsurf | `mcp_config.json` |

---

## Usage

### Start IDA Plugin

1. Open IDA Pro
2. Load a binary file
3. Go to **Edit → Plugins → IDA-Script-MCP** (or press `Ctrl+Alt+S`)
4. The plugin starts an HTTP server:
   ```
   [IDA-Script-MCP] Server started at http://127.0.0.1:13338
   [IDA-Script-MCP] Instance ID: 12345_crackme.exe
   ```

### Start MCP Server

```bash
# stdio transport (for Claude Desktop, etc.)
ida-script-mcp

# HTTP transport
ida-script-mcp --transport http --port 8765

# Specify instance
ida-script-mcp --ida-instance "crackme.exe"
```

---

## MCP Tools

### `list_ida_instances`

List all running IDA instances.

### `execute_idapython`

Execute Python code in IDA context.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | no* | Python code to execute |
| `script_path` | string | no* | Path to script file |
| `instance_id` | string | no | Target instance ID |
| `port` | int | no | Target instance port |

*Either `code` or `script_path` is required

**Example:**
```python
# Execute on default instance
execute_idapython(code="print(idaapi.get_root_filename())")

# Specify instance
execute_idapython(code="...", instance_id="crackme.exe")
execute_idapython(code="...", port=13339)
```

### `check_ida_connection`

Check connection to all IDA instances.

### `get_ida_database_info`

Get info about an IDA database.

---

## Available IDA Modules

- `idaapi` - Core IDA API
- `idc` - IDA C-style API
- `idautils` - IDA utilities
- `ida_bytes`, `ida_funcs`, `ida_name`, `ida_segment`
- `ida_hexrays` - Hex-Rays decompiler
- `ida_kernwin` - IDA kernel/windowing
- `ida_xref`, `ida_typeinf`, and more

---

## Security Notes

- Plugin binds to localhost (127.0.0.1) by default
- Only use with trusted AI assistants
- Don't expose HTTP port to public networks

---

## License

MIT License

---

**中文文档**: 请参阅 [README.md](README.md)
