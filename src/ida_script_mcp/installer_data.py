"""Installer data for MCP clients.

This module contains configuration paths for various MCP clients.
"""

import os
import sys


CLIENT_ALIASES: dict[str, str] = {
    "vscode": "VS Code",
    "vs-code": "VS Code",
    "claude-desktop": "Claude",
    "claude-app": "Claude",
    "claude-code": "Claude Code",
    "cursor": "Cursor",
}

PROJECT_LEVEL_CONFIGS: dict[str, tuple[str, str]] = {
    "Claude Code": ("", ".mcp.json"),
    "Cursor": (".cursor", "mcp.json"),
    "VS Code": (".vscode", "mcp.json"),
    "Windsurf": (".windsurf", "mcp.json"),
}

PROJECT_SPECIAL_JSON_STRUCTURES: dict[str, tuple[str | None, str]] = {
    "VS Code": (None, "servers"),
}

GLOBAL_SPECIAL_JSON_STRUCTURES: dict[str, tuple[str | None, str]] = {
    "VS Code": ("mcp", "servers"),
}


def get_global_configs() -> dict[str, tuple[str, str]]:
    """Get global MCP client configurations for current platform."""
    if sys.platform == "win32":
        return {
            "Claude": (
                os.path.join(os.getenv("APPDATA", ""), "Claude"),
                "claude_desktop_config.json",
            ),
            "Cursor": (
                os.path.join(os.path.expanduser("~"), ".cursor"),
                "mcp.json",
            ),
            "Claude Code": (
                os.path.join(os.path.expanduser("~")),
                ".claude.json",
            ),
            "VS Code": (
                os.path.join(os.getenv("APPDATA", ""), "Code", "User"),
                "settings.json",
            ),
            "Windsurf": (
                os.path.join(os.path.expanduser("~"), ".codeium", "windsurf"),
                "mcp_config.json",
            ),
        }
    elif sys.platform == "darwin":
        return {
            "Claude": (
                os.path.join(
                    os.path.expanduser("~"), "Library", "Application Support", "Claude"
                ),
                "claude_desktop_config.json",
            ),
            "Cursor": (
                os.path.join(os.path.expanduser("~"), ".cursor"),
                "mcp.json",
            ),
            "Claude Code": (
                os.path.join(os.path.expanduser("~")),
                ".claude.json",
            ),
            "VS Code": (
                os.path.join(
                    os.path.expanduser("~"),
                    "Library",
                    "Application Support",
                    "Code",
                    "User",
                ),
                "settings.json",
            ),
            "Windsurf": (
                os.path.join(os.path.expanduser("~"), ".codeium", "windsurf"),
                "mcp_config.json",
            ),
        }
    elif sys.platform == "linux":
        return {
            "Claude": (
                os.path.join(os.path.expanduser("~"), ".config", "Claude"),
                "claude_desktop_config.json",
            ),
            "Cursor": (
                os.path.join(os.path.expanduser("~"), ".cursor"),
                "mcp.json",
            ),
            "Claude Code": (
                os.path.join(os.path.expanduser("~")),
                ".claude.json",
            ),
            "VS Code": (
                os.path.join(os.path.expanduser("~"), ".config", "Code", "User"),
                "settings.json",
            ),
            "Windsurf": (
                os.path.join(os.path.expanduser("~"), ".codeium", "windsurf"),
                "mcp_config.json",
            ),
        }
    return {}


def get_project_configs(project_dir: str) -> dict[str, tuple[str, str]]:
    """Get project-level MCP client configurations."""
    result = {}
    for name, (subdir, config_file) in PROJECT_LEVEL_CONFIGS.items():
        config_dir = os.path.join(project_dir, subdir) if subdir else project_dir
        result[name] = (config_dir, config_file)
    return result


def resolve_client_name(input_name: str, available_clients: list[str]) -> str | None:
    """Resolve client name from alias or partial match."""
    lower_input = input_name.strip().lower()
    for client in available_clients:
        if client.lower() == lower_input:
            return client
    if lower_input in CLIENT_ALIASES:
        alias_target = CLIENT_ALIASES[lower_input]
        if alias_target in available_clients:
            return alias_target
    matches = [c for c in available_clients if lower_input in c.lower()]
    if len(matches) == 1:
        return matches[0]
    return None
