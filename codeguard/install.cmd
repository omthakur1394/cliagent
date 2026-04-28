@echo off
echo.
echo 🛡️  Installing CodeGuard...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Downloading Python installer...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo Installing Python silently...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    echo Python installed successfully!
)

:: Install codeguard
echo Installing CodeGuard...
pip install codeguard-ai

:: Verify
codeguard --help >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ✅ CodeGuard installed successfully!
    echo.
    echo Run it with:
    echo   codeguard
    echo.
) else (
    echo ❌ Installation failed.
)