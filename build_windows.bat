@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo GDoeSII DOE Tools - Windows EXE Build
echo ==========================================
echo.

set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 (
    py -3.13 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.13"
)
if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        python --version >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)
if not defined PYTHON_CMD (
    echo ERROR: No usable Python installation was found.
    echo Install 64-bit Python 3.13 and ensure python.exe is available in PATH.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/6] Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo [1/6] Virtual environment already exists.
)

echo [2/6] Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [3/6] Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [4/6] Running tests...
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto :error

echo [5/6] Building DOE Generator EXE...
".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm config\GDoeSII_DOE_Generator.spec
if errorlevel 1 goto :error

echo [6/6] Building Film GS Batch EXE...
".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm config\GDoeSII_Film_GS_Batch.spec
if errorlevel 1 goto :error

if not exist "dist\GDoeSII_DOE_Generator.exe" goto :error
if not exist "dist\GDoeSII_Film_GS_Batch.exe" goto :error

echo.
echo SUCCESS:
echo   %CD%\dist\GDoeSII_DOE_Generator.exe
echo   %CD%\dist\GDoeSII_Film_GS_Batch.exe
PAUSE
exit /b 0

:error
echo.
echo BUILD FAILED
PAUSE
exit /b 1
