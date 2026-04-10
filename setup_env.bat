@echo off
REM ──────────────────────────────────────────────────────────
REM  py2femm Setup — One-time environment configuration
REM
REM  Steps:
REM    1. Scan for Python + conda (PATH + common install dirs)
REM    2. Choose Python environment (existing conda env or new venv)
REM    3. Activate env + install dependencies
REM    4. Detect FEMM installation and save config/default.yml
REM
REM  Run this ONCE before using start_femm.bat.
REM ──────────────────────────────────────────────────────────

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   py2femm Environment Setup
echo ============================================================

REM ══════════════════════════════════════════════════════════
REM  Step 1: Scan for Python and conda installations
REM ══════════════════════════════════════════════════════════
echo.
echo [1/4] Scanning for Python and conda installations...

set "HAS_PYTHON=0"
set "HAS_CONDA=0"
set "CONDA_BAT="
set "CONDA_ROOT="

REM ── Try conda on PATH first ──────────────────────────────
call conda --version >nul 2>&1
if not errorlevel 1 (
    set "HAS_CONDA=1"
    for /f "delims=" %%V in ('call conda --version 2^>^&1') do echo       [OK] %%V ^(on PATH^)
    for /f "delims=" %%P in ('where conda.bat 2^>nul') do (
        for %%Q in ("%%~dpP..") do set "CONDA_ROOT=%%~fQ"
    )
    goto :conda_found
)

REM ── Scan common conda install locations ──────────────────
echo       conda not on PATH, scanning common locations...
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
    "C:\tools\miniconda3"
    "C:\tools\Anaconda3"
) do (
    if exist "%%~D\condabin\conda.bat" (
        set "HAS_CONDA=1"
        set "CONDA_BAT=%%~D\condabin\conda.bat"
        set "CONDA_ROOT=%%~D"
        echo       [OK] conda found: %%~D
        goto :conda_found
    )
)
echo       conda not found.

:conda_found

REM ── Initialize conda if found via scan (not on PATH) ─────
if defined CONDA_BAT (
    if exist "!CONDA_ROOT!\condabin\conda_hook.bat" (
        call "!CONDA_ROOT!\condabin\conda_hook.bat"
    )
)

REM ── Try python on PATH ───────────────────────────────────
python --version >nul 2>&1
if not errorlevel 1 (
    set "HAS_PYTHON=1"
    for /f "delims=" %%V in ('python --version 2^>^&1') do echo       [OK] %%V
    goto :python_found
)

REM ── Scan common Python install locations ─────────────────
echo       python not on PATH, scanning...
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "C:\Python313"
    "C:\Python312"
    "C:\Python311"
    "C:\Python310"
) do (
    if exist "%%~D\python.exe" (
        set "HAS_PYTHON=1"
        echo       [OK] Python found: %%~D
        set "PATH=%%~D;%%~D\Scripts;!PATH!"
        goto :python_found
    )
)

if "%HAS_CONDA%"=="1" (
    set "HAS_PYTHON=1"
    echo       [OK] Python available via conda.
)

:python_found

if "%HAS_PYTHON%"=="0" if "%HAS_CONDA%"=="0" (
    echo.
    echo [ERROR] No Python or conda installation found.
    echo   Install one of these:
    echo     - Python: https://www.python.org/downloads/
    echo     - Miniconda: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo.

REM ══════════════════════════════════════════════════════════
REM  Step 2: Choose Python environment
REM ══════════════════════════════════════════════════════════
echo [2/4] Python environment selection...
echo.

set "ENV_TYPE="
set "ENV_NAME="

echo       [debug] HAS_CONDA=[%HAS_CONDA%] HAS_PYTHON=[%HAS_PYTHON%] CONDA_ROOT=[%CONDA_ROOT%]

set "HAS_VENV=0"
if exist ".venv\Scripts\activate.bat" set "HAS_VENV=1"
echo       [debug] HAS_VENV=[%HAS_VENV%]

set "CONDA_COUNT=0"
if "%HAS_CONDA%"=="1" (
    echo   Available conda environments:
    echo       [debug] running: conda env list
    for /f "tokens=1,*" %%A in ('call conda env list 2^>nul ^| findstr /v /c:"#" ^| findstr /r /v "^$"') do (
        set /a CONDA_COUNT+=1
        echo     !CONDA_COUNT!. %%A  ^(raw=[%%A] rest=[%%B]^)
        set "CONDA_ENV_!CONDA_COUNT!=%%A"
    )
    if "!CONDA_COUNT!"=="0" echo     ^(none found^)
    echo.
)
echo       [debug] CONDA_COUNT=[!CONDA_COUNT!]

if "%HAS_VENV%"=="1" (
    echo   Existing .venv found.
    echo.
)

echo   Options:
if "%HAS_CONDA%"=="1" if not "!CONDA_COUNT!"=="0" (
    echo     [C] Use existing conda environment
)
if "%HAS_VENV%"=="1" (
    echo     [V] Use existing .venv
) else (
    echo     [V] Create new .venv
)
echo.

set "DEFAULT_CHOICE=V"
if "%HAS_CONDA%"=="1" set "DEFAULT_CHOICE=C"

set "ENV_CHOICE="
set /p "ENV_CHOICE=  Choose [C=conda, V=venv] [%DEFAULT_CHOICE%]: "
if not defined ENV_CHOICE set "ENV_CHOICE=%DEFAULT_CHOICE%"
if /i "%ENV_CHOICE%"=="c" set "ENV_CHOICE=C"
if /i "%ENV_CHOICE%"=="v" set "ENV_CHOICE=V"

echo       [debug] ENV_CHOICE=[%ENV_CHOICE%]

if /i "%ENV_CHOICE%"=="C" goto :choose_conda
goto :choose_venv

:choose_conda
set "ENV_TYPE=conda"
echo       [debug] entered :choose_conda
echo.
set "CONDA_SEL=1"
set /p "CONDA_SEL=  Conda env name or number [1]: "
if not defined CONDA_SEL set "CONDA_SEL=1"
echo       [debug] CONDA_SEL=[!CONDA_SEL!]
call set "ENV_NAME=%%CONDA_ENV_!CONDA_SEL!%%"
echo       [debug] after lookup ENV_NAME=[!ENV_NAME!]
if "!ENV_NAME!"=="" set "ENV_NAME=!CONDA_SEL!"
echo       Selected: conda ^(!ENV_NAME!^)
goto :env_chosen

:choose_venv
set "ENV_TYPE=venv"
set "ENV_NAME="
echo       [debug] entered :choose_venv
echo       Selected: venv
goto :env_chosen

:env_chosen
echo       [debug] env_chosen: ENV_TYPE=[%ENV_TYPE%] ENV_NAME=[%ENV_NAME%]

REM ══════════════════════════════════════════════════════════
REM  Step 3: Activate environment + install dependencies
REM ══════════════════════════════════════════════════════════
echo.
echo [3/4] Setting up environment...
echo       [debug] step3 reached: ENV_TYPE=[%ENV_TYPE%] ENV_NAME=[%ENV_NAME%]

if "%ENV_TYPE%"=="conda" (
    echo       Activating conda env: %ENV_NAME%
    call conda activate %ENV_NAME%
    if errorlevel 1 (
        echo [ERROR] Failed to activate conda env '%ENV_NAME%'.
        pause
        exit /b 1
    )
) else (
    if not exist ".venv\Scripts\activate.bat" (
        echo       Creating .venv...
        python -m venv .venv
        if errorlevel 1 (
            echo [ERROR] Failed to create .venv.
            pause
            exit /b 1
        )
    )
    call .venv\Scripts\activate.bat
)

echo       Installing dependencies...
python -m pip install --quiet --upgrade pip 2>nul

REM Detect Python version to warn about torch 2.5.1 pin (requires <=3.12)
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set "PYVER=%%V"
echo       [debug] PYVER=[%PYVER%]

REM Prefer minimal deps — the library does NOT need torch/pymoo/matplotlib/scipy.
REM Those are only for ML optimization examples.
set "REQ_FILE="
if exist "requirements-min.txt" set "REQ_FILE=requirements-min.txt"
if not defined REQ_FILE if exist "requirements.txt" set "REQ_FILE=requirements.txt"

if defined REQ_FILE (
    echo       Installing %REQ_FILE% ^(core library + server^)...
    python -m pip install -r %REQ_FILE%
    if errorlevel 1 (
        echo       [WARN] %REQ_FILE% install had errors. Continuing anyway.
    ) else (
        echo       %REQ_FILE% installed.
    )
)

REM Install py2femm itself in editable mode if pyproject present
if exist "pyproject.toml" (
    python -m pip install --quiet -e .
    if errorlevel 1 (
        echo       [WARN] editable install failed.
    ) else (
        echo       py2femm installed editable.
    )
)

REM pyFEMM ActiveX wrapper ^(Windows only^) — optional but recommended
python -m pip install --quiet pyfemm 2>nul
if not errorlevel 1 echo       pyfemm installed.

REM ══════════════════════════════════════════════════════════
REM  Step 4: Detect FEMM installation
REM ══════════════════════════════════════════════════════════
echo.
echo [4/4] Detecting FEMM installation...
echo       [debug] step4 reached

set "FEMM_EXE="
for %%D in (
    "C:\femm42\bin\femm.exe"
    "C:\Program Files\femm42\bin\femm.exe"
    "C:\Program Files (x86)\femm42\bin\femm.exe"
    "%USERPROFILE%\femm42\bin\femm.exe"
) do (
    if exist %%D (
        set "FEMM_EXE=%%~D"
        echo       [OK] FEMM found: %%~D
        goto :femm_found
    )
)

echo       FEMM not found in common locations.
set /p "FEMM_EXE=  Enter full path to femm.exe: "
if not exist "!FEMM_EXE!" (
    echo [ERROR] File not found: !FEMM_EXE!
    pause
    exit /b 1
)

:femm_found
echo       [debug] FEMM_EXE=[%FEMM_EXE%]

REM ── Save config/default.yml (pure batch, no yaml dep) ───
echo       [debug] writing yaml with ENV_TYPE=[%ENV_TYPE%] ENV_NAME=[%ENV_NAME%]
if not exist "config" mkdir config
(
    echo python:
    echo   env_type: %ENV_TYPE%
    echo   env_name: %ENV_NAME%
    echo   conda_root: %CONDA_ROOT%
    echo femm:
    echo   exe: %FEMM_EXE%
) > "config\default.yml"

if not exist "config\default.yml" (
    echo [ERROR] Failed to write config\default.yml.
    pause
    exit /b 1
)

echo       config\default.yml saved:
type "config\default.yml"

echo.
echo ============================================================
echo   Setup complete! Run start_femm.bat to launch.
echo ============================================================
echo.
pause
