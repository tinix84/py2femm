@echo off
REM ----------------------------------------------------------
REM  run_liquid_cooler.bat
REM  One-click: starts FEMM server + JupyterLab → liquid_cooler notebook
REM ----------------------------------------------------------
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ── Read config/default.yml ───────────────────────────────
set "CONDA_ROOT="
set "ENV_NAME="
if exist "config\default.yml" (
    for /f "usebackq tokens=2 delims=: " %%V in (`findstr "env_name:"  "config\default.yml"`) do set "ENV_NAME=%%V"
    for /f "usebackq tokens=1,* delims=: " %%A in (`findstr "conda_root:" "config\default.yml"`) do set "CONDA_ROOT=%%B"
    if defined CONDA_ROOT for /f "tokens=*" %%T in ("!CONDA_ROOT!") do set "CONDA_ROOT=%%T"
)

if not defined CONDA_ROOT (
    echo [ERROR] conda_root not found in config\default.yml. Run setup_femm.bat first.
    pause & exit /b 1
)
echo [1/4] Config: env=!ENV_NAME!  conda=!CONDA_ROOT!

REM ── Find jupyter-lab (active env first, then CONDA_ROOT base) ─
set "JUPYTER=!CONDA_ROOT!\Scripts\jupyter-lab.exe"
if not exist "!JUPYTER!" (
    echo [ERROR] jupyter-lab.exe not found at !JUPYTER!
    pause & exit /b 1
)
echo [2/4] jupyter-lab: !JUPYTER!

REM ── Start FEMM server if not already running ─────────────
set "FEMM_EXE="
if exist "config\default.yml" (
    for /f "usebackq tokens=1,* delims=: " %%A in (`findstr "exe:" "config\default.yml"`) do set "FEMM_EXE=%%B"
    if defined FEMM_EXE for /f "tokens=*" %%T in ("!FEMM_EXE!") do set "FEMM_EXE=%%T"
)
"!CONDA_ROOT!\python.exe" -c "import urllib.request; urllib.request.urlopen('http://localhost:8082/api/v1/health',timeout=2)" >nul 2>&1
if errorlevel 1 (
    echo [3/4] Starting FEMM server ...
    start "FEMM Server" /min "!CONDA_ROOT!\python.exe" -m py2femm_server --port 8082 --femm-path "!FEMM_EXE!"
    echo       Waiting 10 s for server ...
    timeout /t 10 /nobreak >nul
    "!CONDA_ROOT!\python.exe" -c "import urllib.request; urllib.request.urlopen('http://localhost:8082/api/v1/health',timeout=3)" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Server not responding yet -- it may still be starting.
    ) else (
        echo       Server OK.
    )
) else (
    echo [3/4] FEMM server already running.
)

REM ── Launch JupyterLab ─────────────────────────────────────
echo [4/4] Opening JupyterLab ...
echo        Notebook: examples\heatflow\liquid_cooler_to247\liquid_cooler.ipynb
echo.
"!JUPYTER!" --notebook-dir=. examples\heatflow\liquid_cooler_to247\liquid_cooler.ipynb

echo.
echo JupyterLab stopped.
pause
