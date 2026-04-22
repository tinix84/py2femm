@echo off
REM ----------------------------------------------------------
REM  Launch JupyterLab in the heatflow examples folder
REM
REM  Opens heatsink/ and liquid_cooler_to247/ notebooks.
REM  Requires: py2femm server running (start_femm_server.bat)
REM ----------------------------------------------------------

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM -- Read Python environment config --
set "ENV_TYPE=venv"
set "ENV_NAME="
set "CONDA_ROOT="
if exist "config\default.yml" (
    for /f "usebackq tokens=2 delims=: " %%V in (`findstr "env_type:" "config\default.yml"`) do set "ENV_TYPE=%%V"
    for /f "usebackq tokens=2 delims=: " %%V in (`findstr "env_name:" "config\default.yml"`) do set "ENV_NAME=%%V"
    for /f "usebackq tokens=1,* delims=: " %%A in (`findstr "conda_root:" "config\default.yml"`) do set "CONDA_ROOT=%%B"
    if defined CONDA_ROOT for /f "tokens=*" %%T in ("!CONDA_ROOT!") do set "CONDA_ROOT=%%T"
)

REM -- Bootstrap conda if needed --
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
        "%LOCALAPPDATA%\miniconda3"
        "%LOCALAPPDATA%\anaconda3"
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

if "%ENV_TYPE%"=="conda" (
    echo Activating conda env: !ENV_NAME!
    call conda activate !ENV_NAME!
    if errorlevel 1 (
        echo [ERROR] Failed to activate conda env. Run setup_femm.bat.
        pause
        exit /b 1
    )
) else (
    if not exist ".venv\Scripts\activate.bat" (
        echo [ERROR] .venv not found. Run setup_femm.bat first.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
)

REM -- Launch JupyterLab --
echo.
echo Starting JupyterLab in examples/heatflow/
echo (Make sure py2femm server is running: start_femm_server.bat)
echo.

REM Try active env first, then fall back to CONDA_ROOT base env
where jupyter-lab >nul 2>&1
if errorlevel 1 (
    if defined CONDA_ROOT (
        if exist "!CONDA_ROOT!\Scripts\jupyter-lab.exe" (
            echo [INFO] Using base conda jupyter-lab: !CONDA_ROOT!\Scripts\jupyter-lab.exe
            "!CONDA_ROOT!\Scripts\jupyter-lab.exe" --notebook-dir=examples\heatflow
        ) else (
            echo [ERROR] jupyter-lab not found. Install it: conda install -n !ENV_NAME! jupyterlab
            pause
            exit /b 1
        )
    )
) else (
    jupyter-lab --notebook-dir=examples\heatflow
)

echo.
echo JupyterLab stopped. Press any key to exit.
pause
