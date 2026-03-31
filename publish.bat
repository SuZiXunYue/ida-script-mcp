@echo off
REM Build and publish to PyPI
REM Usage: publish.bat [test|prod]

setlocal

echo ========================================
echo IDA Script MCP Build and Publish Script
echo ========================================
echo.

REM Check argument
set TARGET=%1
if "%TARGET%"=="" set TARGET=test

REM Clean old builds
echo [1/5] Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist src\ida_script_mcp.egg-info rmdir /s /q src\ida_script_mcp.egg-info
echo Done.
echo.

REM Build
echo [2/5] Building package...
python -m build
if errorlevel 1 (
    echo Error: Build failed!
    exit /b 1
)
echo Done.
echo.

REM Check
echo [3/5] Checking package...
twine check dist/*
if errorlevel 1 (
    echo Error: Package check failed!
    exit /b 1
)
echo Done.
echo.

REM Show files
echo [4/5] Built files:
dir /b dist
echo.

REM Upload
echo [5/5] Uploading to %TARGET%PyPI...
if "%TARGET%"=="prod" (
    twine upload dist/*
) else (
    twine upload --repository testpypi dist/*
)
if errorlevel 1 (
    echo Error: Upload failed!
    exit /b 1
)

echo.
echo ========================================
echo Published successfully!
echo ========================================
if "%TARGET%"=="prod" (
    echo Package URL: https://pypi.org/project/ida-script-mcp/
) else (
    echo Package URL: https://test.pypi.org/project/ida-script-mcp/
    echo.
    echo Install with:
    echo pip install --index-url https://test.pypi.org/simple/ ida-script-mcp
)
echo.

endlocal
