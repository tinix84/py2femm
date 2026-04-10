@echo off
REM ──────────────────────────────────────────────────────────
REM  Start FEMM GUI + py2femm REST API
REM
REM  Reads FEMM path and Python env from config/default.yml
REM  (set by setup_env.bat). Run setup_env.bat first.
REM ──────────────────────────────────────────────────────────

setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist "config\default.yml" (
    echo [ERROR] config\default.yml not found. Run setup_env.bat first.
    pause
    exit /b 1
)

REM ── Read config via python (after env is activated below) ──
REM First pass: raw parse for bootstrap (env type + conda root)
set "ENV_TYPE=venv"
set "ENV_NAME="
set "CONDA_ROOT="
for /f "usebackq tokens=2 delims=: " %%V in (`findstr /c:"env_type:" "config\default.yml"`) do set "ENV_TYPE=%%V"
for /f "usebackq tokens=2 delims=: " %%V in (`findstr /c:"env_name:" "config\default.yml"`) do set "ENV_NAME=%%V"
for /f "usebackq tokens=1,* delims=: " %%A in (`findstr /c:"conda_root:" "config\default.yml"`) do set "CONDA_ROOT=%%B"
if defined CONDA_ROOT for /f "tokens=*" %%T in ("!CONDA_ROOT!") do set "CONDA_ROOT=%%T"

REM ── Bootstrap: ensure conda is available if not on PATH ──
call conda --version >nul 2>&1
if errorlevel 1 (
    if defined CONDA_ROOT (
        if exist "!CONDA_ROOT!\condabin\conda_hook.bat" (
            call "!CONDA_ROOT!\condabin\conda_hook.bat"
            goto :conda_ready
        )
    )
    for %%D in (
        "%USERPROFILE%\miniconda3"
        "%USERPROFILE%\anaconda3"
        "%USERPROFILE%\Miniconda3"
        "%USERPROFILE%\Anaconda3"
        "%LOCALAPPDATA%\miniconda3"
        "%LOCALAPPDATA%\anaconda3"
        "%PROGRAMDATA%\miniconda3"
        "%PROGRAMDATA%\Anaconda3"
        "C:\miniconda3"
        "C:\anaconda3"
    ) do (
        if exist "%%~D\condabin\conda_hook.bat" (
            call "%%~D\condabin\conda_hook.bat"
            goto :conda_ready
        )
    )
)
:conda_ready

REM ── Activate environment ─────────────────────────────────
if "%ENV_TYPE%"=="conda" (
    echo Activating conda env: !ENV_NAME!
    call conda activate !ENV_NAME!
    if errorlevel 1 (
        echo [ERROR] Failed to activate conda env '!ENV_NAME!'. Run setup_env.bat.
        pause
        exit /b 1
    )
) else (
    if not exist ".venv\Scripts\activate.bat" (
        echo [ERROR] .venv not found. Run setup_env.bat first.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
)

REM ── Read FEMM path from yaml: find line '  exe: <path>' and strip prefix ─
REM Line format: "  exe: C:\path\femm.exe" — strip 7 chars ("  exe: ")
set "FEMM_EXE="
for /f "usebackq tokens=* delims=" %%L in (`findstr /r /c:"^  exe:" "config\default.yml"`) do (
    set "LINE=%%L"
    set "FEMM_EXE=!LINE:~7!"
)
echo       [debug] FEMM_EXE=[!FEMM_EXE!]

if not defined FEMM_EXE (
    echo [ERROR] Could not read FEMM path from config/default.yml.
    echo         Run setup_env.bat to configure.
    pause
    exit /b 1
)

if not exist "%FEMM_EXE%" (
    echo [ERROR] FEMM not found at: %FEMM_EXE%
    echo         Re-run setup_env.bat.
    pause
    exit /b 1
)

REM ── Launch FEMM ──────────────────────────────────────────
echo [1/2] Starting FEMM: %FEMM_EXE%
start "" "%FEMM_EXE%"

echo       Waiting 5 seconds for FEMM to initialize...
timeout /t 5 /nobreak > nul

REM ── Launch py2femm REST API (FastAPI via uvicorn) ────────
REM Ignore user-site (AppData\Roaming\Python\...) to avoid loading
REM packages from outside the active conda env.
set "PYTHONNOUSERSITE=1"
echo [2/2] Starting py2femm REST API on 0.0.0.0:8082...
echo       (Press Ctrl+C to stop)
echo.
python -m uvicorn py2femm.femm_server:app --host 0.0.0.0 --port 8082

echo.
echo py2femm API stopped. Press any key to exit.
pause
