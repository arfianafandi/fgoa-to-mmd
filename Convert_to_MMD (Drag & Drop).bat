@echo off
chcp 65001 >nul
title FGO Arcade to MMD Model Converter
color 0B

echo ================================================================
echo           FGO ARCADE TO MMD MODEL CONVERTER TOOL
echo ================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%fgoa_to_mmd.py"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python tidak terdeteksi di sistem Anda!
    echo Silakan install Python 3 dan centang "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM If file or folder was dragged and dropped
if not "%~1"=="" (
    echo [*] Memproses input: "%~1"
    echo.
    python "%PYTHON_SCRIPT%" "%~1"
    echo.
    echo ================================================================
    echo [*] Selesai! Model MMD siap digunakan.
    echo ================================================================
    echo.
    pause
    exit /b 0
)

REM If run by double clicking, prompt user for path
echo Petunjuk:
echo Anda bisa Drag and Drop folder model atau file .pmx ke file .bat ini,
echo atau ketik/paste path folder model di bawah ini:
echo.
set /p "TARGET_PATH=Masukkan Path Folder atau File PMX: "

if "%TARGET_PATH%"=="" (
    echo [!] Tidak ada path yang dimasukkan. Membatalkan.
    pause
    exit /b 0
)

REM Remove surrounding quotes if any
set TARGET_PATH=%TARGET_PATH:"=%

echo.
echo [*] Memproses: "%TARGET_PATH%"
echo.
python "%PYTHON_SCRIPT%" "%TARGET_PATH%"
echo.
echo ================================================================
echo [*] Selesai! Model MMD siap digunakan.
echo ================================================================
echo.
pause
