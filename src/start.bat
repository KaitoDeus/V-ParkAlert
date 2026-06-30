@echo off
echo ==================================================
echo        V-ParkAlert Src Server
echo ==================================================

set "SRC_DIR=%~dp0"
set "ROOT_DIR=%SRC_DIR%.."

:: Set PYTHONPATH so that 'src' module can be imported from anywhere
set "PYTHONPATH=%ROOT_DIR%"

if not exist "%SRC_DIR%.venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment...
    python -m venv "%SRC_DIR%.venv"
) else (
    echo [1/4] Virtual environment exists. Skipping.
)

set "PYTHON=%SRC_DIR%.venv\Scripts\python"
set "PIP=%SRC_DIR%.venv\Scripts\pip"

echo [2/4] Installing dependencies...
"%PIP%" install -r "%SRC_DIR%requirements.txt" -q

echo [3/4] Initializing database...
"%PYTHON%" -m src.init_db

echo [4/4] Starting Src server...
echo ==================================================
"%PYTHON%" -m src.main
pause
