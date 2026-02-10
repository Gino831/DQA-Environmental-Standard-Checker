@echo off
chcp 65001 >nul
title DQA Environmental Standard Checker

echo ╔════════════════════════════════════════════════════════╗
echo ║     DQA Environmental Standard Checker                 ║
echo ║     法規標準檢查系統                                   ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未偵測到 Python，請先安裝 Python 3.x
    pause
    exit /b 1
)

echo [啟動中] 正在啟動伺服器...
echo [資訊] 伺服器位址: http://127.0.0.1:8000
echo.
echo [提示] 按 Ctrl+C 可停止伺服器
echo ─────────────────────────────────────────────────────────
echo.

REM 啟動伺服器並在 2 秒後開啟瀏覽器
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

REM 啟動 Python 伺服器
python server.py

echo.
echo [已停止] 伺服器已關閉
pause
