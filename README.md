# IDA Script MCP

**[English](#english)** | **[中文](#chinese)**

---

<span id="english"></span>
## English Version

Execute IDAPython scripts in IDA Pro through any MCP-compatible AI assistant.

### Why IDA Script MCP?

| | IDA Script MCP |
|---|---|
| **Latency** | < 1ms per request (local HTTP, no IPC overhead) |
| **Footprint** | Zero external dependencies inside IDA — stdlib-only plugin |
| **Startup** | Plugin ready instantly, no background process in IDA |
| **Concurrency** | Run N IDA instances, each on its own port, zero conflict |
| **API Coverage** | Full access to 40+ IDA modules including Hex-Rays decompiler |

The IDA-side plugin uses only Python stdlib (`http.server`, `socket`, `json`) — no pip packages needed inside IDA Pro. The MCP server (separate process) uses `FastMCP` for the protocol layer and communicates with IDA via plain HTTP on localhost. This means:

- No slow startup inside IDA
- No dependency conflicts with IDA's bundled Python
- No memory overhead from heavy frameworks loaded into IDA
- Each IDA instance is completely independent — one crash doesn't affect others

### Features

- **AI-Powered Analysis** — Let any MCP-compatible AI assistant analyze binaries directly in IDA Pro
- **Multi-Instance Support** — Analyze multiple binaries simultaneously across different IDA instances with automatic port assignment
- **Async Task Execution** — Long-running scripts won't disconnect the client; poll for results with configurable timeout
- **One-Command Setup** — Install IDA plugin + configure your AI client in a single step
- **Full IDA API Access** — Complete access to all IDA modules (idaapi, idc, idautils, ida_hexrays, etc.)
- **Jupyter-style Evaluation** — Last expression is automatically returned as the result value
- **Output Capture** — Capture stdout/stderr and return values from executed code
- **Universal Client Support** — Works with any MCP-compatible AI client (see [Supported Clients](#supported-mcp-clients))

### Requirements

- **IDA Pro 8.3+** (IDA Free does not support plugins)
- **Python 3.11+**
- Windows / macOS / Linux

### Installation

#### Option 1: pip (Recommended)

```bash
pip install ida-script-mcp
ida-script-mcp-install install claude
```

#### Option 2: uv

```bash
uv pip install ida-script-mcp
ida-script-mcp-install install claude
```

#### Option 3: pipx (isolated environment)

```bash
pipx install ida-script-mcp
ida-script-mcp-install install claude
```

#### Option 4: From Source

```bash
git clone https://github.com/SuZiXunYue/ida-script-mcp.git
cd ida-script-mcp
pip install -e .
ida-script-mcp-install install
```

#### Advanced Options

```bash
# Install plugin only (no client configuration)
ida-script-mcp-install install

# Configure multiple MCP clients at once
ida-script-mcp-install install claude,cursor,cline

# Use project-level configuration (per-repo settings)
ida-script-mcp-install install --project claude

# List all available MCP clients
ida-script-mcp-install --list-clients

# Print raw MCP config JSON (for manual configuration)
ida-script-mcp-install --config

# Uninstall everything
ida-script-mcp-install uninstall claude
```

### Usage

#### 1. Start IDA Plugin

1. Open IDA Pro and load a binary file
2. Go to **Edit → Plugins → IDA-Script-MCP** (or press `Ctrl+Alt+S`)
3. Plugin will start and show:
   ```
   [IDA-Script-MCP] Server started at http://127.0.0.1:13338
   [IDA-Script-MCP] Instance ID: 12345_crackme.exe
   [IDA-Script-MCP] Database: crackme.exe
   ```

#### 2. Use with AI Assistant

The MCP server provides these tools to your AI assistant:

| Tool | Description |
|------|-------------|
| `list_ida_instances` | List all running IDA instances with ports and database info |
| `execute_idapython` | Execute Python code in IDA Pro (supports `instance_id`, `port`, and `timeout`) |
| `check_ida_connection` | Check connection status and health of all IDA instances |
| `get_ida_database_info` | Get database name, path, and platform info |
| `check_task_status` | Check the status of a long-running script execution task |

#### Long-Running Scripts

By default, `execute_idapython` waits up to 600 seconds for a script to complete, polling the IDA plugin for progress. If the script takes longer, a `task_id` is returned:

```json
{
  "task_id": "a1b2c3d4",
  "status": "running",
  "message": "Script execution timed out after 600s. Use check_task_status with task_id 'a1b2c3d4' to check result later."
}
```

You can then use `check_task_status` to query the result once the script finishes:

```
check_task_status(task_id="a1b2c3d4")
```

You can also customize the timeout:

```
execute_idapython(code="long_analysis()", timeout=1800)
```

#### 3. Example Commands for AI

Ask your AI assistant to:

- "List all functions in this binary"
- "Decompile the main function"
- "Find all xrefs to address 0x401000"
- "Rename function at 0x401000 to my_function"
- "Show all strings in the binary"

### Supported MCP Clients

**This plugin supports all MCP-compatible clients.** The installer provides automatic configuration for the following popular clients:

| Client | Install Command | Config File |
|--------|----------------|-------------|
| Claude Desktop | `ida-script-mcp-install install claude` | `claude_desktop_config.json` |
| Claude Code | `ida-script-mcp-install install claude-code` | `.claude.json` |
| Cursor | `ida-script-mcp-install install cursor` | `.cursor/mcp.json` |
| VS Code | `ida-script-mcp-install install vscode` | `settings.json` |
| Windsurf | `ida-script-mcp-install install windsurf` | `mcp_config.json` |

#### Additional Popular MCP Clients (Manual Configuration)

The following clients are not auto-configured by the installer yet, but work perfectly with IDA Script MCP. Add the config snippet below to the client's MCP settings file:

| Client | Config Location |
|--------|----------------|
| Cline (VS Code extension) | VS Code `settings.json` → `cline.mcpServers` |
| Roo Code (VS Code extension) | `.roo/mcp.json` |
| Trae | Trae MCP settings |
| Augment | Augment MCP settings |
| Continue | `~/.continue/config.json` |
| Copilot (MCP mode) | VS Code `settings.json` → `mcp.servers` |
| Amazon Q Developer | Q Developer MCP settings |
| Aider | `.aider.conf.yml` |
| Any MCP-compatible client | Client's MCP config file |

**Manual config snippet** (add to your client's MCP servers section):

```json
{
  "mcpServers": {
    "ida-script-mcp": {
      "command": "python",
      "args": ["-m", "ida_script_mcp.server"]
    }
  }
}
```

If you're using a virtual environment, replace `"python"` with the full path:

```bash
# Find your Python path
python -c "import sys; print(sys.executable)"
```

#### Configure Multiple Clients at Once

```bash
ida-script-mcp-install install claude,cursor,vscode,windsurf
```

### Troubleshooting

**Plugin not found in IDA**
- Ensure plugin file is in IDA's plugins directory
- Check IDA output window for errors
- Re-run `ida-script-mcp-install install`

**Connection refused**
- Verify IDA Pro is running with a database loaded
- Confirm plugin is started (Edit → Plugins → IDA-Script-MCP)
- Check that the port matches in `~/.ida_script_mcp_instances.json`

**Multiple instances route to wrong IDA**
- This was a Windows-specific bug fixed in v1.0.1 — ensure you're on the latest version
- Each IDA instance should get a unique port (13338, 13339, 13340, ...)

**Script times out / client disconnects**
- Long-running scripts now use async task execution — the server polls for results instead of blocking
- If you see a `task_id` in the response, use `check_task_status` to query the result later
- Adjust the `timeout` parameter (default: 600s) if your script needs more time:
  ```
  execute_idapython(code="slow_analysis()", timeout=1800)
  ```

**Command not found**
```bash
pip show ida-script-mcp
which ida-script-mcp-install
```

### Security Note

This plugin allows arbitrary Python code execution in IDA Pro:
- Use only with trusted AI assistants
- Plugin binds to `127.0.0.1` by default (localhost only)
- Never expose the HTTP port to public networks

### License

MIT License

### Changelog

#### [1.2.0] - 2026-05-08

**Added:**
- **Async task execution system**: Long-running scripts no longer cause client disconnection. Scripts are submitted asynchronously to IDA, and the MCP server polls for completion with exponential backoff (0.5s → 5s cap). If the configurable timeout (default: 600s) is exceeded, a `task_id` is returned for later status queries.
- **`check_task_status` tool**: New MCP tool to query the status and result of a long-running script execution task by its `task_id`.
- **`timeout` parameter for `execute_idapython`**: Configurable maximum wait time (default: 600 seconds) before returning a `task_id` for deferred polling.
- **Task management endpoints in IDA plugin**: `GET /task/{id}` to query task status/result, `GET /tasks` to list all tasks.
- **`async` mode for `POST /execute`**: IDA plugin now accepts `{"async": true}` to submit scripts for background execution and immediately return a `task_id`.
- **ThreadingMixIn HTTP server**: The IDA plugin HTTP server now handles each request in a separate thread, preventing a single long-running script from blocking other requests (e.g., health checks, task status queries).

**Fixed:**
- **Client disconnection on long-running scripts**: Previously, scripts running longer than 60 seconds would cause the MCP server's HTTP connection to IDA to time out, while the script continued running in IDA with no way to retrieve the result. The new async task system eliminates this issue.
- **HTTP server blocking**: The IDA plugin's single-threaded HTTP server could be blocked by a running script, making all other endpoints (health, metadata) unreachable. Switched to `ThreadingMixIn` for concurrent request handling.

#### [1.1.0] - 2026-04-16

**Fixed:**
- **Windows multi-instance port collision**: On Windows, all IDA instances would bind to the same port (13338) because `SO_REUSEADDR` allows multiple processes to bind the same port without error. Fixed by disabling `allow_reuse_address` on Windows and adding pre-bind port detection.

#### [1.0.0] - 2024-01-15

**Added:**
- Initial release with `list_ida_instances`, `execute_idapython`, `check_ida_connection`, `get_ida_database_info` tools.
- Multi-instance support, auto-discovery, full IDA API access, Jupyter-style evaluation, cross-platform support.

---

<span id="chinese"></span>
## 中文版本

通过任何支持 MCP 协议的 AI 助手，在 IDA Pro 中执行 IDAPython 脚本。

### 为什么选择 IDA Script MCP？

| | IDA Script MCP |
|---|---|
| **延迟** | 每次请求 < 1ms（本地 HTTP，无 IPC 开销） |
| **资源占用** | IDA 内零外部依赖 — 插件仅使用标准库 |
| **启动速度** | 插件即时就绪，IDA 内无后台进程 |
| **并发能力** | 运行 N 个 IDA 实例，各自独立端口，互不冲突 |
| **API 覆盖** | 完整访问 40+ IDA 模块，包括 Hex-Rays 反编译器 |

IDA 端插件仅使用 Python 标准库（`http.server`、`socket`、`json`）——无需在 IDA Pro 中安装任何 pip 包。MCP 服务器（独立进程）使用 `FastMCP` 作为协议层，通过本地 HTTP 与 IDA 通信。这意味着：

- IDA 内无缓慢启动
- 不与 IDA 内置 Python 产生依赖冲突
- 不因加载重框架而占用 IDA 内存
- 每个 IDA 实例完全独立 — 一个崩溃不影响其他

### 特性

- **AI 驱动分析** — 让任何支持 MCP 的 AI 助手直接在 IDA Pro 中分析二进制文件
- **多实例支持** — 同时分析多个二进制文件，自动分配端口，实例间互不干扰
- **异步任务执行** — 长时间运行的脚本不会导致客户端断开连接；可配置超时，轮询获取结果
- **一键安装** — 一条命令完成 IDA 插件安装和 AI 客户端配置
- **完整 IDA API 访问** — 完全访问所有 IDA 模块（idaapi、idc、idautils、ida_hexrays 等）
- **Jupyter 风格求值** — 自动返回最后一个表达式的值
- **输出捕获** — 捕获执行代码的标准输出/错误和返回值
- **通用客户端支持** — 兼容所有支持 MCP 协议的客户端（见[支持客户端](#支持的-mcp-客户端-1)）

### 系统要求

- **IDA Pro 8.3+**（IDA Free 不支持插件）
- **Python 3.11+**
- Windows / macOS / Linux

### 安装

#### 方式一：pip（推荐）

```bash
pip install ida-script-mcp
ida-script-mcp-install install claude
```

#### 方式二：uv

```bash
uv pip install ida-script-mcp
ida-script-mcp-install install claude
```

#### 方式三：pipx（隔离环境）

```bash
pipx install ida-script-mcp
ida-script-mcp-install install claude
```

#### 方式四：从源码安装

```bash
git clone https://github.com/SuZiXunYue/ida-script-mcp.git
cd ida-script-mcp
pip install -e .
ida-script-mcp-install install
```

#### 高级选项

```bash
# 仅安装插件（不配置客户端）
ida-script-mcp-install install

# 同时配置多个 MCP 客户端
ida-script-mcp-install install claude,cursor,cline

# 使用项目级配置（每个仓库独立设置）
ida-script-mcp-install install --project claude

# 列出所有可用的 MCP 客户端
ida-script-mcp-install --list-clients

# 打印 MCP 配置 JSON（用于手动配置）
ida-script-mcp-install --config

# 卸载
ida-script-mcp-install uninstall claude
```

### 使用方法

#### 1. 启动 IDA 插件

1. 打开 IDA Pro 并加载二进制文件
2. 进入 **Edit → Plugins → IDA-Script-MCP**（或按 `Ctrl+Alt+S`）
3. 插件启动后会显示：
   ```
   [IDA-Script-MCP] Server started at http://127.0.0.1:13338
   [IDA-Script-MCP] Instance ID: 12345_crackme.exe
   [IDA-Script-MCP] Database: crackme.exe
   ```

#### 2. 使用 AI 助手

MCP 服务器为 AI 助手提供以下工具：

| 工具 | 说明 |
|------|------|
| `list_ida_instances` | 列出所有运行中的 IDA 实例及其端口和数据库信息 |
| `execute_idapython` | 在 IDA Pro 中执行 Python 代码（支持 `instance_id`、`port` 和 `timeout`） |
| `check_ida_connection` | 检查所有 IDA 实例的连接状态和健康信息 |
| `get_ida_database_info` | 获取数据库名称、路径和平台信息 |
| `check_task_status` | 查询长时间运行的脚本执行任务的状态 |

#### 长时间运行的脚本

默认情况下，`execute_idapython` 最多等待 600 秒让脚本完成，期间会轮询 IDA 插件获取进度。如果脚本执行时间超过该限制，会返回一个 `task_id`：

```json
{
  "task_id": "a1b2c3d4",
  "status": "running",
  "message": "Script execution timed out after 600s. Use check_task_status with task_id 'a1b2c3d4' to check result later."
}
```

脚本完成后，可使用 `check_task_status` 查询结果：

```
check_task_status(task_id="a1b2c3d4")
```

也可以自定义超时时间：

```
execute_idapython(code="long_analysis()", timeout=1800)
```

#### 3. 示例命令

让 AI 助手执行：

- "列出此二进制文件中的所有函数"
- "反编译 main 函数"
- "查找地址 0x401000 的所有交叉引用"
- "将地址 0x401000 的函数重命名为 my_function"
- "显示二进制文件中的所有字符串"

### 支持的 MCP 客户端

**本插件支持所有兼容 MCP 协议的客户端。** 安装器为以下常用客户端提供自动配置：

| 客户端 | 安装命令 | 配置文件 |
|--------|---------|---------|
| Claude Desktop | `ida-script-mcp-install install claude` | `claude_desktop_config.json` |
| Claude Code | `ida-script-mcp-install install claude-code` | `.claude.json` |
| Cursor | `ida-script-mcp-install install cursor` | `.cursor/mcp.json` |
| VS Code | `ida-script-mcp-install install vscode` | `settings.json` |
| Windsurf | `ida-script-mcp-install install windsurf` | `mcp_config.json` |

#### 更多常用 MCP 客户端（手动配置）

以下客户端暂未纳入安装器自动配置，但完全兼容 IDA Script MCP。将下方配置片段添加到客户端的 MCP 设置中即可：

| 客户端 | 配置位置 |
|--------|---------|
| Cline（VS Code 扩展） | VS Code `settings.json` → `cline.mcpServers` |
| Roo Code（VS Code 扩展） | `.roo/mcp.json` |
| Trae | Trae MCP 设置 |
| Augment | Augment MCP 设置 |
| Continue | `~/.continue/config.json` |
| Copilot（MCP 模式） | VS Code `settings.json` → `mcp.servers` |
| Amazon Q Developer | Q Developer MCP 设置 |
| Aider | `.aider.conf.yml` |
| 任何支持 MCP 的客户端 | 客户端 MCP 配置文件 |

**手动配置片段**（添加到客户端的 MCP 服务器配置中）：

```json
{
  "mcpServers": {
    "ida-script-mcp": {
      "command": "python",
      "args": ["-m", "ida_script_mcp.server"]
    }
  }
}
```

如果使用虚拟环境，将 `"python"` 替换为完整路径：

```bash
# 查看 Python 路径
python -c "import sys; print(sys.executable)"
```

#### 同时配置多个客户端

```bash
ida-script-mcp-install install claude,cursor,vscode,windsurf
```

### 故障排除

**在 IDA 中找不到插件**
- 确认插件文件在 IDA 的 plugins 目录中
- 检查 IDA 输出窗口的错误信息
- 重新运行 `ida-script-mcp-install install`

**连接被拒绝**
- 确保 IDA Pro 正在运行且已加载数据库
- 确认插件已启动（Edit → Plugins → IDA-Script-MCP）
- 检查 `~/.ida_script_mcp_instances.json` 中的端口是否正确

**多实例路由到错误的 IDA**
- 这是 Windows 上的已知问题，已在 v1.0.1 中修复 — 请确保使用最新版本
- 每个 IDA 实例应获得唯一端口（13338、13339、13340……）

**脚本超时 / 客户端断开**
- 长时间运行的脚本现在使用异步任务执行 — 服务器会轮询获取结果而非阻塞等待
- 如果响应中包含 `task_id`，可使用 `check_task_status` 稍后查询结果
- 可通过 `timeout` 参数调整等待时间（默认 600 秒）：
  ```
  execute_idapython(code="slow_analysis()", timeout=1800)
  ```

**找不到命令**
```bash
pip show ida-script-mcp
which ida-script-mcp-install
```

### 安全提示

此插件允许在 IDA Pro 中执行任意 Python 代码：
- 仅与可信的 AI 助手一起使用
- 插件默认绑定到 `127.0.0.1`（仅本地访问）
- 切勿将 HTTP 端口暴露到公网

### 许可证

MIT License

### 更新日志

#### [1.2.0] - 2026-05-08

**新增：**
- **异步任务执行系统**：长时间运行的脚本不再导致客户端断开连接。脚本异步提交到 IDA，MCP 服务器以指数退避策略（0.5s → 5s 上限）轮询完成状态。如果超过可配置的超时时间（默认 600 秒），会返回 `task_id` 供后续查询。
- **`check_task_status` 工具**：新增 MCP 工具，通过 `task_id` 查询长时间运行的脚本执行任务的状态和结果。
- **`execute_idapython` 的 `timeout` 参数**：可配置最大等待时间（默认 600 秒），超时后返回 `task_id` 以便延迟轮询。
- **IDA 插件任务管理端点**：`GET /task/{id}` 查询任务状态/结果，`GET /tasks` 列出所有任务。
- **`POST /execute` 的 `async` 模式**：IDA 插件现在接受 `{"async": true}` 以提交脚本进行后台执行，并立即返回 `task_id`。
- **ThreadingMixIn HTTP 服务器**：IDA 插件 HTTP 服务器现在在独立线程中处理每个请求，防止单个长时间运行的脚本阻塞其他请求（如健康检查、任务状态查询）。

**修复：**
- **长时间运行脚本导致客户端断开**：此前，运行超过 60 秒的脚本会导致 MCP 服务器到 IDA 的 HTTP 连接超时，而脚本在 IDA 中继续运行但无法获取结果。新的异步任务系统解决了此问题。
- **HTTP 服务器阻塞**：IDA 插件的单线程 HTTP 服务器可被运行中的脚本阻塞，导致所有其他端点（health、metadata）不可达。改用 `ThreadingMixIn` 实现并发请求处理。

#### [1.1.0] - 2026-04-16

**修复：**
- **Windows 多实例端口冲突**：在 Windows 上，所有 IDA 实例会绑定到同一端口 (13338)，因为 `SO_REUSEADDR` 允许多个进程无错误地绑定同一端口。通过在 Windows 上禁用 `allow_reuse_address` 并添加绑定前端口检测来修复。

#### [1.0.0] - 2024-01-15

**新增：**
- 初始发布，包含 `list_ida_instances`、`execute_idapython`、`check_ida_connection`、`get_ida_database_info` 工具。
- 多实例支持、自动发现、完整 IDA API 访问、Jupyter 风格求值、跨平台支持。
