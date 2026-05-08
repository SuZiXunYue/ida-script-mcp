"""Tests for IDA Script MCP."""

import pytest
import os
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ida_script_mcp.server import (
    ExecuteScriptInput,
    get_ida_host,
    get_ida_port,
    list_instances,
)
from ida_script_mcp.installer import (
    get_python_executable,
    _get_ida_user_dir,
    generate_mcp_config,
)


class TestExecuteScriptInput:
    """Tests for ExecuteScriptInput model."""
    
    def test_code_only(self):
        """Test with code only."""
        params = ExecuteScriptInput(code="print('hello')")
        assert params.code == "print('hello')"
        assert params.script_path is None
        assert params.capture_output is True
    
    def test_script_path_only(self):
        """Test with script path only."""
        params = ExecuteScriptInput(script_path="/path/to/script.py")
        assert params.code is None
        assert params.script_path == "/path/to/script.py"
        assert params.capture_output is True
    
    def test_both_code_and_path(self):
        """Test with both code and script path."""
        params = ExecuteScriptInput(
            code="print('hello')",
            script_path="/path/to/script.py",
        )
        assert params.code == "print('hello')"
        assert params.script_path == "/path/to/script.py"
    
    def test_capture_output_false(self):
        """Test with capture_output=False."""
        params = ExecuteScriptInput(code="print('hello')", capture_output=False)
        assert params.capture_output is False
    
    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from code."""
        params = ExecuteScriptInput(code="  print('hello')  ")
        assert params.code == "print('hello')"
    
    def test_instance_id(self):
        """Test instance_id parameter."""
        params = ExecuteScriptInput(code="print('hello')", instance_id="crackme.exe")
        assert params.instance_id == "crackme.exe"
    
    def test_port_parameter(self):
        """Test port parameter."""
        params = ExecuteScriptInput(code="print('hello')", port=13339)
        assert params.port == 13339
    
    def test_timeout_default(self):
        """Test default timeout value."""
        params = ExecuteScriptInput(code="print('hello')")
        assert params.timeout == 600
    
    def test_timeout_custom(self):
        """Test custom timeout value."""
        params = ExecuteScriptInput(code="print('hello')", timeout=120)
        assert params.timeout == 120


class TestConfiguration:
    """Tests for configuration functions."""
    
    def test_default_host(self):
        """Test default host value."""
        os.environ.pop("IDA_SCRIPT_MCP_HOST", None)
        assert get_ida_host() == "127.0.0.1"
    
    def test_default_port(self):
        """Test default port value."""
        os.environ.pop("IDA_SCRIPT_MCP_PORT", None)
        assert get_ida_port() is None
    
    def test_env_host(self):
        """Test host from environment."""
        os.environ["IDA_SCRIPT_MCP_HOST"] = "192.168.1.1"
        assert get_ida_host() == "192.168.1.1"
        os.environ.pop("IDA_SCRIPT_MCP_HOST")
    
    def test_env_port(self):
        """Test port from environment."""
        os.environ["IDA_SCRIPT_MCP_PORT"] = "8080"
        assert get_ida_port() == 8080
        os.environ.pop("IDA_SCRIPT_MCP_PORT")


class TestListInstances:
    """Tests for list_instances function."""
    
    def test_list_instances_empty(self):
        """Test list_instances when no instances file exists."""
        # This should return empty dict if no instances file
        result = list_instances()
        assert isinstance(result, dict)


class TestInstaller:
    """Tests for installer functions."""
    
    def test_get_python_executable(self):
        """Test get_python_executable returns a valid path."""
        result = get_python_executable()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_ida_user_dir(self):
        """Test _get_ida_user_dir returns a valid path."""
        result = _get_ida_user_dir()
        assert isinstance(result, str)
        if sys.platform == "win32":
            assert "Hex-Rays" in result or "IDA Pro" in result
        else:
            assert ".idapro" in result
    
    def test_generate_mcp_config(self):
        """Test generate_mcp_config returns valid config."""
        result = generate_mcp_config(client_name="Claude")
        assert "command" in result
        assert "args" in result
        assert isinstance(result["args"], list)
