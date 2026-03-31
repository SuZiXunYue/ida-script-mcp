#!/bin/bash
# Build and publish to PyPI
# Usage: ./publish.sh [test|prod]

set -e

echo "========================================"
echo "IDA Script MCP Build and Publish Script"
echo "========================================"
echo

# Check argument
TARGET=${1:-test}

# Clean old builds
echo "[1/5] Cleaning old builds..."
rm -rf dist/ build/ src/ida_script_mcp.egg-info/
echo "Done."
echo

# Build
echo "[2/5] Building package..."
python -m build
echo "Done."
echo

# Check
echo "[3/5] Checking package..."
twine check dist/*
echo "Done."
echo

# Show files
echo "[4/5] Built files:"
ls -la dist/
echo

# Upload
echo "[5/5] Uploading to ${TARGET}PyPI..."
if [ "$TARGET" = "prod" ]; then
    twine upload dist/*
else
    twine upload --repository testpypi dist/*
fi

echo
echo "========================================"
echo "Published successfully!"
echo "========================================"
if [ "$TARGET" = "prod" ]; then
    echo "Package URL: https://pypi.org/project/ida-script-mcp/"
else
    echo "Package URL: https://test.pypi.org/project/ida-script-mcp/"
    echo
    echo "Install with:"
    echo "pip install --index-url https://test.pypi.org/simple/ ida-script-mcp"
fi
echo
