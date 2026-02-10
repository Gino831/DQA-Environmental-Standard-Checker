@echo off
chcp 65001 >nul
title DQA Environmental Standard Checker - 一鍵安裝與啟動
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║     🌿 DQA Environmental Standard Checker                    ║
echo ║        法規標準檢查系統 - 一鍵安裝與啟動                     ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 檢查 Python 是否安裝
echo [1/3] 檢查 Python 環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ╔══════════════════════════════════════════════════════════════╗
    echo ║  ❌ 錯誤: 未偵測到 Python                                    ║
    echo ║                                                              ║
    echo ║  請先至 https://www.python.org/downloads/ 下載安裝 Python   ║
    echo ║  安裝時請勾選 "Add Python to PATH"                          ║
    echo ╚══════════════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)
echo      ✓ Python 已安裝
for /f "tokens=*" %%i in ('python --version') do echo      版本: %%i

REM 安裝相依套件
echo.
echo [2/3] 安裝相依套件...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo      ⚠ 安裝套件時發生警告，嘗試繼續...
) else (
    echo      ✓ 套件安裝完成
)

REM 啟動伺服器
echo.
echo [3/3] 啟動應用程式...
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  ✓ 伺服器啟動成功！                                          ║
echo ║                                                              ║
echo ║  🌐 請開啟瀏覽器訪問: http://127.0.0.1:8001                  ║
echo ║                                                              ║
echo ║  💡 提示: 按 Ctrl+C 可停止伺服器                             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 2秒後自動開啟瀏覽器
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8001"

REM 啟動 Python 伺服器
python server.py

echo.
echo ═══════════════════════════════════════════════════════════════
echo   伺服器已關閉，感謝使用！
echo ═══════════════════════════════════════════════════════════════
pause
