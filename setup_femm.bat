@echo off
REM ----------------------------------------------------------
REM  py2femm Setup - One-time environment configuration
REM
REM  Steps:
REM    1. Scan for Python + conda
REM    2. Choose Python environment
REM    3. Activate env + install dependencies
REM    4. Configure FEMM path and workspace
REM
REM  Settings saved to config/default.yml.
REM  Run this ONCE before using start_femm_server.bat.
REM ----------------------------------------------------------

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   py2femm Server Setup
echo ============================================================

REM Step 1: Scan for Python and conda
echo.
echo [1/4] Scanning for Python and conda...

set "HAS_PYTHON=0"
set "HAS_CONDA=0"
set "CONDA_ROOT="

call conda --version >nul 2>&1
if not errorlevel 1 (
    set "HAS_CONDA=1"
    for /f "delims=" %%V in ('call conda --version 2^>^&1') do echo       [OK] %%V
    for /f "delims=" %%P in ('where conda.bat 2^>nul') do (
        for %%Q in ("%%~dpP..") do set "CONDA_ROOT=%%~fQ"
    )
    goto :conda_found
)

echo       conda not on PATH, scanning...
for %%D in (
    "%USERPROFILE%\miniconda3"
    "%USERPROFILE%\anaconda3"
    "%LOCALAPPDATA%\miniconda3"
    "%LOCALAPPDATA%\anaconda3"
    "C:\miniconda3"
    "C:\anaconda3"
) do (
    if exist "%%~D\condabin\conda.bat" (
        set "HAS_CONDA=1"
        set "CONDA_ROOT=%%~D"
        echo       [OK] conda found: %%~D
        goto :conda_found
    )
)
echo       conda not found.

:conda_found

if defined CONDA_ROOT (
    if exist "!CONDA_ROOT!\condabin\conda_hook.bat" (
        call "!CONDA_ROOT!\condabin\conda_hook.bat"
    )
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "HAS_PYTHON=1"
    for /f "delims=" %%V in ('python --version 2^>^&1') do echo       [OK] %%V
    goto :python_found
)

for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
) do (
    if exist "%%~D\python.exe" (
        set "HAS_PYTHON=1"
        set "PATH=%%~D;%%~D\Scripts;!PATH!"
        echo       [OK] Python found: %%~D
        goto :python_found
    )
)

if "%HAS_CONDA%"=="1" set "HAS_PYTHON=1"

:python_found

if "%HAS_PYTHON%"=="0" if "%HAS_CONDA%"=="0" (
    echo [ERROR] No Python or conda found.
    echo   Install from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Step 2: Choose environment
echo.
echo [2/4] Python environment...

set "ENV_TYPE=venv"

if "%HAS_CONDA%"=="1" (
    set /p "USE_CONDA=  Use conda environment? [y/N]: "
    if /i "!USE_CONDA!"=="y" (
        set "ENV_TYPE=conda"
        set /p "ENV_NAME=  Conda env name [py2femm]: "
        if not defined ENV_NAME set "ENV_NAME=py2femm"
    )
)

REM Step 3: Activate + install
echo.
echo [3/4] Installing dependencies...

if "%ENV_TYPE%"=="conda" (
    call conda activate %ENV_NAME% 2>nul || (
        echo       Creating conda env %ENV_NAME%...
        call conda create -n %ENV_NAME% python=3.11 -y
        call conda activate %ENV_NAME%
    )
) else (
    if not exist ".venv\Scripts\activate.bat" (
        echo       Creating .venv...
        python -m venv .venv
    )
    call .venv\Scripts\activate.bat
)

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e ".[agent]"
echo       [OK] py2femm[server] installed.

REM Step 4: Configure FEMM
echo.
echo [4/4] Configuring FEMM...

python -c "import yaml; from pathlib import Path; p=Path('config/default.yml'); p.parent.mkdir(exist_ok=True); cfg=yaml.safe_load(p.read_text()) if p.exists() else {}; cfg.setdefault('python',{}); cfg['python']['env_type']='%ENV_TYPE%'; cfg['python']['env_name']='%ENV_NAME%'; cfg['python']['conda_root']=r'%CONDA_ROOT%'; p.write_text(yaml.dump(cfg,default_flow_style=False,sort_keys=False))"

python tools\configure_femm.py
if errorlevel 1 (
    echo [ERROR] FEMM configuration failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Setup complete! Run start_femm_server.bat to launch.
echo ============================================================
echo.
pause
