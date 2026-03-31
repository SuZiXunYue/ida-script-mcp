# IDA Script MCP

一个用于在 IDA Pro 中执行 IDAPython 脚本的 MCP (Model Context Protocol) 服务器。这使得 Claude 等 AI 助手能够直接在 IDA Pro 环境中运行 Python 代码。

## 功能特性

- 在 IDA Pro 环境中执行 Python 代码或脚本文件
- 完整访问所有 IDA API 模块（idaapi、idc、idautils 等）
- 捕获 stdout/stderr 输出
- 支持表达式返回值
- 连接状态监控
- **支持多个 IDA 实例同时运行**（可同时分析多个二进制文件）

## 系统架构

### 单实例模式
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI 助手       │────▶│   MCP 服务器    │────▶│   IDA 插件      │
│   (Claude等)    │     │ (FastMCP/stdio) │     │ (HTTP 服务器)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                      │
                                                      ▼
                                                ┌─────────────────┐
                                                │    IDA Pro      │
                                                │  (主线程执行)    │
                                                └─────────────────┘
```

### 多实例模式
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI 助手       │────▶│   MCP 服务器    │────▶│ IDA实例1:13338  │
│   (Claude等)    │     │ (自动发现实例)   │     │   crackme.exe   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              │                  ┌─────────────────┐
                              └─────────────────▶│ IDA实例2:13339  │
                                                 │   malware.dll   │
                                                 └─────────────────┘
```

## 系统要求

- **IDA Pro 8.3+**（不支持 IDA Free）
- **Python 3.11+**
- 操作系统：Windows / macOS / Linux

---

## 安装步骤

### 方法一：使用安装命令（推荐）

安装 Python 包后，使用 `ida-script-mcp-install` 命令：

```bash
# 1. 安装 Python 包
pip install ida-script-mcp

# 2. 安装 IDA 插件
ida-script-mcp-install install

# 3. 同时配置 MCP 客户端（可选）
ida-script-mcp-install install claude      # 配置 Claude Desktop
ida-script-mcp-install install claude,cursor  # 配置多个客户端

# 查看可用客户端
ida-script-mcp-install --list-clients
```

**完整安装示例：**

```bash
# 安装插件并配置 Claude
pip install ida-script-mcp
ida-script-mcp-install install claude
```

### 方法二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/ida-script-mcp.git
cd ida-script-mcp

# 安装 Python 包（开发模式）
pip install -e .

# 安装 IDA 插件
ida-script-mcp-install install
```

### 方法三：手动安装

如果不想安装 Python 包，可以手动复制插件：

```bash
# 将插件文件复制到 IDA 用户目录
# Windows: %APPDATA%\Hex-Rays\IDA Pro\plugins\
# macOS/Linux: ~/.idapro/plugins/

cp src/ida_script_mcp/ida_plugin.py ~/.idapro/plugins/ida_script_mcp.py
```

---

## 安装命令详解

### `ida-script-mcp-install`

安装工具提供以下功能：

```bash
# 安装 IDA 插件
ida-script-mcp-install install

# 安装插件并配置 MCP 客户端
ida-script-mcp-install install claude
ida-script-mcp-install install claude,cursor,vscode

# 使用项目级配置（而不是全局）
ida-script-mcp-install install --project claude

# 卸载插件
ida-script-mcp-install uninstall

# 列出可用的 MCP 客户端
ida-script-mcp-install --list-clients

# 显示 MCP 配置示例
ida-script-mcp-install --config
```

### 支持的 MCP 客户端

| 客户端 | 配置文件位置 |
|--------|-------------|
| Claude | `claude_desktop_config.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.claude.json` |
| VS Code | `settings.json` |
| Windsurf | `mcp_config.json` |

---

## 使用方法

### 启动 IDA 插件

1. 打开 IDA Pro
2. 加载一个二进制文件
3. 进入 **Edit → Plugins → IDA-Script-MCP**（或按 `Ctrl+Alt+S`）
4. 插件将启动 HTTP 服务器，显示：
   ```
   [IDA-Script-MCP] Server started at http://127.0.0.1:13338
   [IDA-Script-MCP] Instance ID: 12345_crackme.exe
   [IDA-Script-MCP] Execute endpoint: POST http://127.0.0.1:13338/execute
   ```

### 启动 MCP 服务器

```bash
# 使用 stdio 传输方式（适用于 Claude Desktop 等）
ida-script-mcp

# 使用 HTTP 传输方式
ida-script-mcp --transport http --port 8765

# 指定 IDA 实例
ida-script-mcp --ida-instance "crackme.exe"
```

### 配置 Claude Desktop

安装命令会自动配置，也可以手动添加到配置文件：

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ida-script": {
      "command": "python",
      "args": ["-m", "ida_script_mcp.server"]
    }
  }
}
```

---

## MCP 工具说明

### `list_ida_instances`

列出所有正在运行的 IDA 实例。

**返回值：**
```json
{
  "count": 2,
  "instances": {
    "12345_crackme.exe": {
      "pid": 12345,
      "port": 13338,
      "database": "crackme.exe",
      "database_path": "C:\\analysis\\crackme.exe"
    },
    "67890_malware.dll": {
      "pid": 67890,
      "port": 13339,
      "database": "malware.dll"
    }
  }
}
```

### `execute_idapython`

在 IDA Pro 环境中执行 Python 代码或脚本文件。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code` | string | 否* | 要执行的 Python 代码 |
| `script_path` | string | 否* | Python 脚本文件路径 |
| `capture_output` | boolean | 否 | 是否捕获输出（默认 true） |
| `instance_id` | string | 否 | 目标 IDA 实例 ID（多实例时使用） |
| `port` | int | 否 | 目标 IDA 实例端口（多实例时使用） |

**返回值：**
```json
{
  "result": "表达式返回值",
  "stdout": "标准输出",
  "stderr": "错误输出",
  "instance": "12345_crackme.exe",
  "port": 13338
}
```

**示例：**
```python
# 在默认实例执行代码
code = "print(idaapi.get_root_filename())"

# 指定实例（通过数据库名模糊匹配）
execute_idapython(code="...", instance_id="crackme.exe")

# 指定实例（通过端口）
execute_idapython(code="...", port=13339)
```

### `check_ida_connection`

检查所有 IDA Pro 实例的连接状态。

### `get_ida_database_info`

获取指定 IDA 数据库的信息。

---

## 可用的 IDA 模块

执行代码时，以下模块自动在全局命名空间中可用：

| 模块 | 说明 |
|------|------|
| `idaapi` | IDA Pro 核心 API |
| `idc` | IDA C 风格 API |
| `idautils` | IDA 工具函数 |
| `ida_bytes` | 字节操作 |
| `ida_funcs` | 函数操作 |
| `ida_name` | 名称操作 |
| `ida_segment` | 段操作 |
| `ida_hexrays` | Hex-Rays 反编译器 |
| `ida_kernwin` | IDA 内核/窗口系统 |
| `ida_xref` | 交叉引用 |
| `ida_typeinf` | 类型信息 |

---

## 使用示例

### 列出所有函数
```python
import idautils
import idc

for ea in idautils.Functions():
    name = idc.get_func_name(ea)
    print(f"{hex(ea)}: {name}")
```

### 反编译函数
```python
import ida_hexrays
import ida_funcs
import idc

ea = idc.get_name_ea_simple("main")
func = ida_funcs.get_func(ea)
if func:
    cfunc = ida_hexrays.decompile(func)
    print(str(cfunc))
```

### 重命名函数
```python
import idc

idc.set_name(0x401000, "my_function", idc.SN_NOWARN)
```

### 获取交叉引用
```python
import idautils

for xref in idautils.XrefsTo(0x401000):
    print(f"从 {hex(xref.frm)} 引用到 {hex(xref.to)}")
```

---

## 多实例使用场景

### 场景：同时分析多个二进制文件

当你打开多个 IDA Pro 窗口分析不同的二进制文件时：

```
IDA 实例 1: crackme.exe  -> 端口 13338
IDA 实例 2: malware.dll  -> 端口 13339
IDA 实例 3: payload.bin  -> 端口 13340
```

MCP 服务器会自动发现并管理这些实例。

---

## 故障排除

### 问题：在 IDA 中找不到插件

**解决方案：**
1. 确认插件文件 `ida_script_mcp.py` 在 IDA 的 plugins 目录中
2. 检查 IDA 的 Python 版本是否为 3.11+
3. 查看 IDA 输出窗口的错误信息

### 问题：连接被拒绝

**解决方案：**
1. 确保 IDA Pro 正在运行且已加载数据库
2. 确认插件已启动（Edit → Plugins → IDA-Script-MCP）
3. 检查端口是否正确（默认：13338）

### 问题：找不到命令

**解决方案：**
```bash
# 确认包已安装
pip show ida-script-mcp

# 检查命令路径
which ida-script-mcp-install
```

---

## 安全注意事项

⚠️ **重要提示：**

- 此插件允许在 IDA Pro 中执行任意 Python 代码
- 请仅与可信的 AI 助手一起使用
- 插件默认绑定到 `127.0.0.1`（仅本地访问）
- 不要在公网暴露 HTTP 端口

---

## 许可证

MIT License

## 贡献

欢迎贡献代码！请提交 Issue 或 Pull Request。

---

**英文文档**: 请参阅 [README_EN.md](README_EN.md)
