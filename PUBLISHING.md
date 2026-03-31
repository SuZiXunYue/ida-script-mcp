# 发布到 PyPI 指南

本文档说明如何将 ida-script-mcp 发布到 PyPI。

## 前提条件

### 1. 注册 PyPI 账号

- 正式环境：https://pypi.org/account/register/
- 测试环境：https://test.pypi.org/account/register/

### 2. 创建 API Token

1. 登录 PyPI
2. 进入 Account Settings → API tokens
3. 创建新 token（选择 "Entire account" 或特定项目）
4. **保存 token**（只显示一次）

## 发布步骤

### 步骤 1：安装构建工具

```bash
pip install build twine
```

### 步骤 2：更新版本号

编辑 `pyproject.toml`：

```toml
version = "1.0.1"  # 更新版本号
```

### 步骤 3：更新项目 URL

编辑 `pyproject.toml`，将 `yourusername` 替换为你的 GitHub 用户名：

```toml
[project.urls]
Homepage = "https://github.com/yourusername/ida-script-mcp"
Repository = "https://github.com/yourusername/ida-script-mcp.git"
```

### 步骤 4：构建项目

```bash
cd ida-script-mcp

# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info
rmdir /s /q dist build src\ida_script_mcp.egg-info  # Windows

# 构建
python -m build
```

这将生成：
- `dist/ida_script_mcp-1.0.0.tar.gz` (源码包)
- `dist/ida_script_mcp-1.0.0-py3-none-any.whl` (wheel 包)

### 步骤 5：检查构建结果

```bash
# 检查包
twine check dist/*
```

### 步骤 6：上传到 TestPyPI（可选但推荐）

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ ida-script-mcp
```

### 步骤 7：上传到 PyPI

```bash
twine upload dist/*
```

## 使用 API Token 上传

创建 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-xxx...  # 你的 PyPI token

[testpypi]
username = __token__
password = pypi-xxx...  # 你的 TestPyPI token
```

然后可以直接运行：

```bash
twine upload dist/*
# 或
twine upload --repository testpypi dist/*
```

## 自动化发布（GitHub Actions）

创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install build tools
        run: |
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Check package
        run: twine check dist/*
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

然后在 GitHub 仓库设置中添加 `PYPI_API_TOKEN` secret。

## 版本管理建议

### 语义化版本

遵循 [Semantic Versioning](https://semver.org/)：

- `MAJOR.MINOR.PATCH`（如 `1.0.0`）
- MAJOR：不兼容的 API 更改
- MINOR：向后兼容的功能新增
- PATCH：向后兼容的问题修复

### 更新日志

创建 `CHANGELOG.md` 记录版本更新：

```markdown
# Changelog

## [1.0.0] - 2024-01-15

### Added
- Initial release
- Support for multiple IDA instances
- Auto-discovery of running instances
- Execute IDAPython code via MCP

### Changed
- N/A

### Fixed
- N/A
```

## 检查清单

发布前确认：

- [ ] 更新版本号
- [ ] 更新 CHANGELOG.md
- [ ] 运行测试（如有）
- [ ] 检查文档
- [ ] 构建成功
- [ ] `twine check` 通过
- [ ] TestPyPI 测试安装成功
- [ ] git tag 版本

## 常见问题

### Q: 包名已被占用？

修改 `pyproject.toml` 中的 `name`：

```toml
name = "ida-script-mcp-yourname"
```

### Q: 上传失败：File already exists？

版本号已存在于 PyPI，需要更新版本号后重新上传。

### Q: 依赖版本冲突？

检查 `dependencies` 中的版本约束，确保兼容。

### Q: 需要删除已发布的版本？

PyPI 不允许删除文件，但可以：
1. 在 PyPI 网站上 "yank" 特定版本
2. 发布新版本修复问题

## 相关链接

- [PyPI 文档](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Setuptools 文档](https://setuptools.pypa.io/)
- [Twine 文档](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
