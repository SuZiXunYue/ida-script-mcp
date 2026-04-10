# IDA Script MCP

**[English](#english)** | **[中文](#chinese)**

---

<span id="english"></span>
## 🇺🇸 English Version

Execute IDAPython scripts in IDA Pro through AI assistants like Claude.

### Features

- 🤖 **AI-Powered Analysis** - Let Claude or other AI assistants analyze binaries directly in IDA Pro
- 🔄 **Multi-Instance Support** - Analyze multiple binaries simultaneously across different IDA instances
- 🚀 **Easy Integration** - One-command installation for both IDA plugin and MCP client configuration
- 🔧 **Full IDA API Access** - Complete access to all IDA modules (idaapi, idc, idautils, ida_hexrays, etc.)
- 📊 **Output Capture** - Capture stdout/stderr and return values from executed code

### Requirements

- **IDA Pro 8.3+** (IDA Free not supported)
- **Python 3.11+**
- Windows / macOS / Linux

### Installation

#### Quick Start (Recommended)

```bash
# Install package and configure Claude Desktop
pip install ida-script-mcp
ida-script-mcp-install install claude
```

#### Advanced Options

```bash
# Install plugin only
ida-script-mcp-install install

# Configure multiple MCP clients
ida-script-mcp-install install claude,cursor,vscode

# Use project-level configuration
ida-script-mcp-install install --project claude

# List available MCP clients
ida-script-mcp-install --list-clients
```

#### From Source

```bash
git clone https://github.com/yourusername/ida-script-mcp.git
cd ida-script-mcp
pip install -e .
ida-script-mcp-install install
```

### Usage

#### 1. Start IDA Plugin

1. Open IDA Pro and load a binary file
2. Go to **Edit → Plugins → IDA-Script-MCP** (or press `Ctrl+Alt+S`)
3. Plugin will start and show:
   ```
   [IDA-Script-MCP] Server started at http://127.0.0.1:13338
   [IDA-Script-MCP] Instance ID: 12345_crackme.exe
   ```

#### 2. Use with AI Assistant

The MCP server provides these tools to your AI assistant:

- **`list_ida_instances`** - List all running IDA instances
- **`execute_idapython`** - Execute Python code in IDA Pro
- **`check_ida_connection`** - Check connection status
- **`get_ida_database_info`** - Get database information

#### 3. Example Commands for AI

Ask your AI assistant to:

- "List all functions in this binary"
- "Decompile the main function"
- "Find all xrefs to address 0x401000"
- "Rename function at 0x401000 to my_function"
- "Show all strings in the binary"

### Supported MCP Clients

| Client | Configuration File |
|--------|-------------------|
| Claude Desktop | `claude_desktop_config.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.claude.json` |
| VS Code | `settings.json` |
| Windsurf | `mcp_config.json` |

### Troubleshooting

**Plugin not found in IDA**
- Ensure plugin file is in IDA's plugins directory
- Check IDA output window for errors

**Connection refused**
- Verify IDA Pro is running with a database loaded
- Confirm plugin is started (Edit → Plugins → IDA-Script-MCP)

**Command not found**
```bash
pip show ida-script-mcp
which ida-script-mcp-install
```

### Security Note

⚠️ This plugin allows arbitrary Python code execution in IDA Pro:
- Use only with trusted AI assistants
- Plugin binds to `127.0.0.1` by default (localhost only)
- Never expose the HTTP port to public networks

### License

MIT License

---

<span id="chinese"></span>
## 🇨🇳 中文版本

通过 Claude 等 AI 助手在 IDA Pro 中执行 IDAPython 脚本。

### 特性

- 🤖 **AI 驱动分析** - 让 Claude 或其他 AI 助手直接在 IDA Pro 中分析二进制文件
- 🔄 **多实例支持** - 同时分析多个二进制文件，跨不同 IDA 实例
- 🚀 **简单集成** - 一条命令完成 IDA 插件和 MCP 客户端配置
- 🔧 **完整 IDA API 访问** - 完全访问所有 IDA 模块（idaapi、idc、idautils、ida_hexrays 等）
- 📊 **输出捕获** - 捕获执行代码的标准输出/错误和返回值

### 系统要求

- **IDA Pro 8.3+**（不支持 IDA Free）
- **Python 3.11+**
- Windows / macOS / Linux

### 安装

#### 快速开始（推荐）

```bash
# 安装包并配置 Claude Desktop
pip install ida-script-mcp
ida-script-mcp-install install claude
```

#### 高级选项

```bash
# 仅安装插件
ida-script-mcp-install install

# 配置多个 MCP 客户端
ida-script-mcp-install install claude,cursor,vscode

# 使用项目级配置
ida-script-mcp-install install --project claude

# 列出可用的 MCP 客户端
ida-script-mcp-install --list-clients
```

#### 从源码安装

```bash
git clone https://github.com/yourusername/ida-script-mcp.git
cd ida-script-mcp
pip install -e .
ida-script-mcp-install install
```

### 使用方法

#### 1. 启动 IDA 插件

1. 打开 IDA Pro 并加载二进制文件
2. 进入 **Edit → Plugins → IDA-Script-MCP**（或按 `Ctrl+Alt+S`）
3. 插件启动后会显示：
   ```
   [IDA-Script-MCP] Server started at http://127.0.0.1:13338
   [IDA-Script-MCP] Instance ID: 12345_crackme.exe
   ```

#### 2. 使用 AI 助手

MCP 服务器为 AI 助手提供以下工具：

- **`list_ida_instances`** - 列出所有运行中的 IDA 实例
- **`execute_idapython`** - 在 IDA Pro 中执行 Python 代码
- **`check_ida_connection`** - 检查连接状态
- **`get_ida_database_info`** - 获取数据库信息

#### 3. 示例命令

让 AI 助手执行：

- "列出此二进制文件中的所有函数"
- "反编译 main 函数"
- "查找地址 0x401000 的所有交叉引用"
- "将地址 0x401000 的函数重命名为 my_function"
- "显示二进制文件中的所有字符串"

### 支持的 MCP 客户端

| 客户端 | 配置文件 |
|--------|---------|
| Claude Desktop | `claude_desktop_config.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.claude.json` |
| VS Code | `settings.json` |
| Windsurf | `mcp_config.json` |

### 故障排除

**在 IDA 中找不到插件**
- 确认插件文件在 IDA 的 plugins 目录中
- 检查 IDA 输出窗口的错误信息

**连接被拒绝**
- 确保 IDA Pro 正在运行且已加载数据库
- 确认插件已启动（Edit → Plugins → IDA-Script-MCP）

**找不到命令**
```bash
pip show ida-script-mcp
which ida-script-mcp-install
```

### 安全提示

⚠️ 此插件允许在 IDA Pro 中执行任意 Python 代码：
- 仅与可信的 AI 助手一起使用
- 插件默认绑定到 `127.0.0.1`（仅本地访问）
- 切勿将 HTTP 端口暴露到公网

### 许可证

MIT License
