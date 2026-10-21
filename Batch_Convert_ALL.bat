@echo off
chcp 65001 >nul
title Batch Convert All FGOA Models to MMD
color 0E

echo ================================================================
echo       BATCH CONVERT ALL FGO ARCADE MODELS TO MMD
echo ================================================================
echo.
echo Tool ini akan memindai seluruh folder di E:\FGO\FGOA
echo dan mengonversi semua model yang ditemukan secara otomatis.
echo.
set /p "CONFIRM=Apakah Anda yakin ingin memproses semua model? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo [!] Dibatalkan oleh pengguna.
    pause
    exit /b 0
)

echo.
echo [*] Memulai batch convert untuk seluruh E:\FGO\FGOA...
echo.

set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%fgoa_to_mmd.py" --all "E:\FGO\FGOA"

echo.
echo ================================================================
echo [*] Seluruh proses konversi batch selesai!
echo ================================================================
echo.
pause
