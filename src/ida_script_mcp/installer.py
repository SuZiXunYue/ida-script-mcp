"""IDA Script MCP Installer.

This module provides installation commands for:
1. Installing the IDA Pro plugin
2. Configuring MCP clients (Claude, Cursor, VS Code, etc.)

Usage:
    ida-script-mcp-install install [OPTIONS]
    ida-script-mcp-install uninstall [OPTIONS]
"""

import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

try:
    from .installer_data import (
        get_global_configs,
        get_project_configs,
        resolve_client_name,
        GLOBAL_SPECIAL_JSON_STRUCTURES,
        PROJECT_SPECIAL_JSON_STRUCTURES,
        PROJECT_LEVEL_CONFIGS,
    )
except ImportError:
    from installer_data import (
        get_global_configs,
        get_project_configs,
        resolve_client_name,
        GLOBAL_SPECIAL_JSON_STRUCTURES,
        PROJECT_SPECIAL_JSON_STRUCTURES,
        PROJECT_LEVEL_CONFIGS,
    )


MCP_SERVER_NAME = "ida-script-mcp"
PLUGIN_NAME = "ida_script_mcp"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
IDA_PLUGIN_FILE = os.path.join(SCRIPT_DIR, "ida_plugin.py")
SERVER_SCRIPT = os.path.join(SCRIPT_DIR, "server.py")


def get_python_executable() -> str:
    """Get the Python executable path for MCP config."""
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        if sys.platform == "win32":
            python = os.path.join(venv, "Scripts", "python.exe")
        else:
            python = os.path.join(venv, "bin", "python3")
        if os.path.exists(python):
            return python
    return sys.executable


def _get_ida_user_dir() -> str:
    """Get IDA Pro user directory."""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA", ""), "Hex-Rays", "IDA Pro")
    return os.path.join(os.path.expanduser("~"), ".idapro")


def _remove_path(path: str) -> None:
    """Remove a file or directory."""
    if not os.path.lexists(path):
        return
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def _install_link_or_copy(source: str, destination: str) -> bool:
    """Install by symlink or copy."""
    existing_realpath = (
        os.path.realpath(destination) if os.path.lexists(destination) else None
    )
    if existing_realpath == source:
        return False

    _remove_path(destination)
    try:
        os.symlink(source, destination)
    except OSError:
        shutil.copy(source, destination)
    return True


def is_ida_plugin_installed() -> bool:
    """Check if IDA plugin is installed."""
    ida_folder = _get_ida_user_dir()
    return os.path.lexists(os.path.join(ida_folder, "plugins", f"{PLUGIN_NAME}.py"))


def install_ida_plugin(*, uninstall: bool = False, quiet: bool = False) -> bool:
    """Install or uninstall the IDA Pro plugin.

    Args:
        uninstall: If True, uninstall the plugin
        quiet: If True, suppress output

    Returns:
        True if successful, False otherwise
    """
    ida_folder = _get_ida_user_dir()
    
    free_licenses = glob.glob(os.path.join(ida_folder, "idafree_*.hexlic"))
    if free_licenses and not uninstall:
        print("IDA Free does not support plugins. Please use IDA Pro.")
        return False

    ida_plugin_folder = os.path.join(ida_folder, "plugins")
    plugin_destination = os.path.join(ida_plugin_folder, f"{PLUGIN_NAME}.py")

    if uninstall:
        if os.path.lexists(plugin_destination):
            _remove_path(plugin_destination)
            if not quiet:
                print(f"Uninstalled IDA Pro plugin")
                print(f"  Removed: {plugin_destination}")
        else:
            if not quiet:
                print("IDA plugin not installed, nothing to uninstall")
        return True

    if not os.path.exists(IDA_PLUGIN_FILE):
        print(f"Error: Plugin file not found: {IDA_PLUGIN_FILE}")
        return False

    os.makedirs(ida_plugin_folder, exist_ok=True)
    
    if _install_link_or_copy(IDA_PLUGIN_FILE, plugin_destination):
        if not quiet:
            print("Installed IDA Pro plugin (IDA restart required)")
            print(f"  Plugin: {plugin_destination}")
            print(f"\n  To enable: Edit -> Plugins -> IDA-Script-MCP (Ctrl+Alt+S)")
    else:
        if not quiet:
            print("IDA plugin already up to date")

    return True


def _read_config_file(config_path: str, *, is_toml: bool = False) -> dict | None:
    """Read JSON or TOML config file."""
    try:
        if is_toml:
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            with open(config_path, "rb") as f:
                return tomllib.load(f)
        with open(config_path, "r", encoding="utf-8") as f:
            data = f.read().strip()
            return json.loads(data) if data else {}
    except (json.JSONDecodeError, OSError):
        return None


def _write_config_file(config_path: str, config: dict, *, is_toml: bool = False) -> None:
    """Write JSON or TOML config file."""
    config_dir = os.path.dirname(config_path)
    suffix = ".toml" if is_toml else ".json"
    fd, temp_path = tempfile.mkstemp(
        dir=config_dir, prefix=".tmp_", suffix=suffix, text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            if is_toml:
                try:
                    import tomli_w
                except ImportError:
                    json.dump(config, f, indent=2)
                    return
                f.write(tomli_w.dumps(config))
            else:
                json.dump(config, f, indent=2)
        os.replace(temp_path, config_path)
    except Exception:
        os.unlink(temp_path)
        raise


def _get_mcp_servers_view(
    config: dict,
    *,
    client_name: str,
    is_toml: bool,
    special_json_structures: dict[str, tuple[str | None, str]],
) -> dict:
    """Get the mcpServers section from config."""
    if is_toml:
        return config.setdefault("mcp_servers", {})
    if client_name in special_json_structures:
        top_key, nested_key = special_json_structures[client_name]
        if top_key is None:
            return config.setdefault(nested_key, {})
        return config.setdefault(top_key, {}).setdefault(nested_key, {})
    return config.setdefault("mcpServers", {})


def generate_mcp_config(*, client_name: str) -> dict:
    """Generate MCP configuration for a client."""
    return {
        "command": get_python_executable(),
        "args": ["-m", "ida_script_mcp.server"],
    }


def list_available_clients():
    """List all available MCP clients."""
    configs = get_global_configs()
    if not configs:
        print(f"Unsupported platform: {sys.platform}")
        return

    print("Available MCP clients:\n")
    for name, (config_dir, _) in configs.items():
        supports_project = name in PROJECT_LEVEL_CONFIGS
        project_marker = " [supports --project]" if supports_project else ""
        status = "found" if os.path.exists(config_dir) else "not found"
        print(f"  {name:<20} ({status}){project_marker}")

    print()
    print("Examples:")
    print("  ida-script-mcp-install install                    # Install plugin only")
    print("  ida-script-mcp-install install claude             # Install plugin + Claude config")
    print("  ida-script-mcp-install install claude,cursor      # Multiple clients")
    print("  ida-script-mcp-install install --project          # Project-level config")
    print("  ida-script-mcp-install uninstall                  # Uninstall plugin")
    print("  ida-script-mcp-install list-clients               # List clients")


def install_mcp_client(
    client_name: str,
    *,
    project: bool = False,
    uninstall: bool = False,
    quiet: bool = False,
) -> bool:
    """Install or uninstall MCP client configuration.

    Args:
        client_name: Name of the MCP client
        project: Use project-level config
        uninstall: Uninstall instead of install
        quiet: Suppress output

    Returns:
        True if successful
    """
    if project:
        configs = get_project_configs(os.getcwd())
        special_json_structures = PROJECT_SPECIAL_JSON_STRUCTURES
    else:
        configs = get_global_configs()
        special_json_structures = GLOBAL_SPECIAL_JSON_STRUCTURES

    if not configs:
        print(f"Unsupported platform: {sys.platform}")
        return False

    resolved_name = resolve_client_name(client_name, list(configs.keys()))
    if not resolved_name:
        print(f"Unknown client: '{client_name}'")
        print("Use --list-clients to see available options")
        return False

    config_dir, config_file = configs[resolved_name]
    config_path = os.path.join(config_dir, config_file)
    is_toml = config_file.endswith(".toml")

    if not os.path.exists(config_dir):
        if project and not uninstall:
            os.makedirs(config_dir, exist_ok=True)
        else:
            action = "uninstall" if uninstall else "install"
            if not quiet:
                print(f"Skipping {resolved_name} {action}")
                print(f"  Config directory not found: {config_dir}")
            return False

    config = {}
    if os.path.exists(config_path):
        config = _read_config_file(config_path, is_toml=is_toml) or {}

    mcp_servers = _get_mcp_servers_view(
        config,
        client_name=resolved_name,
        is_toml=is_toml,
        special_json_structures=special_json_structures,
    )

    if uninstall:
        if MCP_SERVER_NAME not in mcp_servers:
            if not quiet:
                print(f"Skipping {resolved_name} uninstall (not configured)")
            return True
        del mcp_servers[MCP_SERVER_NAME]
        action = "Uninstalled"
    else:
        mcp_servers[MCP_SERVER_NAME] = generate_mcp_config(client_name=resolved_name)
        action = "Installed"

    _write_config_file(config_path, config, is_toml=is_toml)
    
    if not quiet:
        print(f"{action} {resolved_name} MCP config (restart required)")
        print(f"  Config: {config_path}")

    return True


def print_mcp_config():
    """Print example MCP configuration."""
    config = {
        "mcpServers": {
            MCP_SERVER_NAME: generate_mcp_config(client_name="Generic"),
        }
    }
    print("[MCP CONFIGURATION]\n")
    print(json.dumps(config, indent=2))
    print("\nAdd this to your MCP client configuration file.")


def main():
    """Main entry point for the installer."""
    parser = argparse.ArgumentParser(
        description="IDA Script MCP Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s install                    Install IDA plugin only
  %(prog)s install claude             Install plugin + configure Claude
  %(prog)s install claude,cursor      Install for multiple clients
  %(prog)s install --project claude   Use project-level config
  %(prog)s uninstall                  Uninstall IDA plugin
  %(prog)s --list-clients             List available MCP clients
  %(prog)s --config                   Show MCP config snippet
        """,
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=["install", "uninstall"],
        default="install",
        help="Action to perform (default: install)",
    )
    parser.add_argument(
        "clients",
        nargs="?",
        type=str,
        default="",
        help="Comma-separated list of MCP clients (e.g., claude,cursor)",
    )
    parser.add_argument(
        "--project",
        action="store_true",
        help="Use project-level configuration instead of global",
    )
    parser.add_argument(
        "--list-clients",
        action="store_true",
        help="List available MCP clients",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Print MCP configuration snippet",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )
    args = parser.parse_args()

    if args.list_clients:
        list_available_clients()
        return

    if args.config:
        print_mcp_config()
        return

    uninstall = args.action == "uninstall"

    if not install_ida_plugin(uninstall=uninstall, quiet=args.quiet):
        sys.exit(1)

    if args.clients:
        client_list = [c.strip() for c in args.clients.split(",") if c.strip()]
        for client in client_list:
            install_mcp_client(
                client,
                project=args.project,
                uninstall=uninstall,
                quiet=args.quiet,
            )

    if not args.clients and not args.quiet:
        print()
        print("To configure an MCP client, run:")
        print(f"  ida-script-mcp-install install <client>")
        print()
        print("Use --list-clients to see available clients")


if __name__ == "__main__":
    main()
