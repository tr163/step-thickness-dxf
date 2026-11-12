@echo off
chcp 65001 >nul
if "%~1"=="" (
    echo Drag STEP files or a folder onto this icon.
    echo DXF output goes to "dxf_out" next to the dropped item.
    pause
    exit /b
)
set "PY=%~dp0python\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0step2dxf.py" %*
pause
