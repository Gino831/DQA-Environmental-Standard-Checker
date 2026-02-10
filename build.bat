@echo off
chcp 65001 >nul
title DQA Standard Checker - 建置 EXE
color 0E

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║     📦 DQA Standard Checker - 建置 EXE 執行檔               ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 檢查 Python
echo [1/4] 檢查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo      ❌ 錯誤: 未偵測到 Python
    pause
    exit /b 1
)
echo      ✓ Python 已安裝

REM 安裝/更新 PyInstaller
echo.
echo [2/4] 安裝 PyInstaller...
pip install pyinstaller --upgrade -q
if errorlevel 1 (
    echo      ⚠ PyInstaller 安裝警告，嘗試繼續...
) else (
    echo      ✓ PyInstaller 已就緒
)

REM 安裝專案相依套件
echo.
echo [3/4] 安裝相依套件...
pip install -r requirements.txt -q
echo      ✓ 相依套件已安裝

REM 執行打包
echo.
echo [4/4] 打包 EXE...
echo      這可能需要 1-3 分鐘，請稍候...
echo.
pyinstaller build_exe.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ╔══════════════════════════════════════════════════════════════╗
    echo ║  ❌ 打包失敗，請檢查上方錯誤訊息                             ║
    echo ╚══════════════════════════════════════════════════════════════╝
    pause
    exit /b 1
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  ✅ 打包完成！                                               ║
echo ║                                                              ║
echo ║  📁 執行檔位置: dist\DQA_Standard_Checker.exe               ║
echo ║                                                              ║
echo ║  📋 使用說明:                                                ║
echo ║     1. 複製 dist\DQA_Standard_Checker.exe 到目標資料夾      ║
echo ║     2. 複製 verify_standards.py 到同一資料夾（一鍵更新需要）║
echo ║     3. 雙擊 exe 啟動應用程式                                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
pause
