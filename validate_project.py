#!/usr/bin/env python3
"""
DQA 環境標準檢查工具 - 自動化驗證腳本
驗證系統實作是否符合 project_plan.md 文件描述
"""

import os
import re
import sys
import json
import importlib.util

# 設定終端機編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 使用 ASCII 符號避免編碼問題
class Symbols:
    PASS = '[PASS]'
    FAIL = '[FAIL]'
    WARN = '[WARN]'

def print_result(passed, message):
    """輸出測試結果"""
    if passed:
        print(f"  {Symbols.PASS} {message}")
    else:
        print(f"  {Symbols.FAIL} {message}")
    return passed

def print_header(title):
    """輸出區段標題"""
    print(f"\n=== {title} ===")

# ============================================
# 1. 檔案結構驗證
# ============================================
def verify_file_structure():
    """驗證所有必要檔案是否存在"""
    print_header("1. 檔案結構驗證")
    
    required_files = {
        'index.html': '前端主頁面',
        'style.css': '前端樣式表',
        'app.js': '前端應用邏輯',
        'data.js': '初始資料 (Source of Truth)',
        'server.py': '後端 HTTP 伺服器',
        'verify_standards.py': '驗證爬蟲腳本',
        'config.js': '設定檔',
        'start_app.bat': '一鍵啟動批次檔',
        'project_plan.md': '專案計畫書',
    }
    
    all_passed = True
    for filename, description in required_files.items():
        exists = os.path.exists(filename)
        all_passed &= print_result(exists, f"{filename} ({description})")
    
    return all_passed

# ============================================
# 2. 後端 API 端點驗證
# ============================================
def verify_api_endpoint():
    """驗證 server.py 中的 API 端點設定"""
    print_header("2. 後端 API 端點驗證")
    
    all_passed = True
    
    try:
        with open('server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查 /api/run-verify 端點
        has_api = "/api/run-verify" in content
        all_passed &= print_result(has_api, "API 端點 /api/run-verify 已定義")
        
        # 檢查使用 subprocess 執行 Python
        has_subprocess = "subprocess.run" in content
        all_passed &= print_result(has_subprocess, "使用 subprocess.run 執行爬蟲")
        
        # 檢查 JSON 回應
        has_json_response = "application/json" in content
        all_passed &= print_result(has_json_response, "回應 Content-Type 為 application/json")
        
        # 檢查呼叫 verify_standards.py
        calls_verify = "verify_standards.py" in content
        all_passed &= print_result(calls_verify, "呼叫 verify_standards.py 腳本")
        
    except Exception as e:
        print_result(False, f"讀取 server.py 失敗: {e}")
        return False
    
    return all_passed

# ============================================
# 3. 爬蟲模組驗證
# ============================================
def verify_crawler_module():
    """驗證爬蟲腳本的依賴與實作"""
    print_header("3. 爬蟲模組驗證")
    
    all_passed = True
    
    # 檢查 requests 模組
    try:
        import requests
        print_result(True, "requests 模組已安裝")
    except ImportError:
        all_passed &= print_result(False, "requests 模組未安裝 (pip install requests)")
    
    # 檢查 BeautifulSoup 模組
    try:
        from bs4 import BeautifulSoup
        print_result(True, "BeautifulSoup 模組已安裝")
    except ImportError:
        all_passed &= print_result(False, "BeautifulSoup 模組未安裝 (pip install beautifulsoup4)")
    
    # 檢查 verify_standards.py 內容
    try:
        with open('verify_standards.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查核心功能
        has_scrape = "def scrape_iec_page" in content
        all_passed &= print_result(has_scrape, "scrape_iec_page() 爬取函數已定義")
        
        has_verify = "def verify_standard_logic" in content
        all_passed &= print_result(has_verify, "verify_standard_logic() 驗證函數已定義")
        
        has_report = "verification_report.md" in content
        all_passed &= print_result(has_report, "生成 verification_report.md 報告")
        
    except Exception as e:
        print_result(False, f"讀取 verify_standards.py 失敗: {e}")
        return False
    
    return all_passed

# ============================================
# 4. 前端實作驗證
# ============================================
def verify_frontend():
    """驗證前端實作是否符合文件"""
    print_header("4. 前端實作驗證")
    
    all_passed = True
    
    # 檢查 index.html
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        has_verify_btn = "Verify" in html_content
        all_passed &= print_result(has_verify_btn, "Verify 按鈕存在於 HTML")
        
    except Exception as e:
        print_result(False, f"讀取 index.html 失敗: {e}")
    
    # 檢查 app.js
    try:
        with open('app.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # 檢查 localStorage 使用
        has_localstorage = "localStorage" in js_content
        all_passed &= print_result(has_localstorage, "使用 localStorage 持久化資料")
        
        # 檢查 API 呼叫
        has_api_call = "/api/run-verify" in js_content
        all_passed &= print_result(has_api_call, "前端呼叫 /api/run-verify 端點")
        
        # 檢查動態渲染
        has_render = "renderStandards" in js_content
        all_passed &= print_result(has_render, "renderStandards() 動態渲染函數")
        
        # 檢查 CRUD 功能
        has_add = "addBtn" in js_content or "addModal" in js_content
        all_passed &= print_result(has_add, "新增 (Add) 功能實作")
        
        has_edit = "editStandard" in js_content
        all_passed &= print_result(has_edit, "編輯 (Edit) 功能實作")
        
        has_delete = "deleteStandard" in js_content
        all_passed &= print_result(has_delete, "刪除 (Delete) 功能實作")
        
    except Exception as e:
        print_result(False, f"讀取 app.js 失敗: {e}")
        return False
    
    return all_passed

# ============================================
# 5. 資料結構驗證
# ============================================
def verify_data_structure():
    """驗證 data.js 的資料結構"""
    print_header("5. 資料結構驗證")
    
    all_passed = True
    required_fields = ['id', 'name', 'cost', 'effectiveDate', 'expiryDate', 'sourceUrl']
    
    try:
        with open('data.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        for field in required_fields:
            has_field = f"'{field}':" in content or f'"{field}":' in content or f"{field}:" in content
            all_passed &= print_result(has_field, f"欄位 '{field}' 存在於資料結構中")
        
    except Exception as e:
        print_result(False, f"讀取 data.js 失敗: {e}")
        return False
    
    return all_passed

# ============================================
# 6. 驗證報告輸出檢查
# ============================================
def verify_output_files():
    """檢查驗證輸出檔案"""
    print_header("6. 驗證輸出檔案")
    
    output_files = [
        ('verification_report.md', '驗證報告 (Markdown)'),
        ('verification_results.json', '驗證結果 (JSON)'),
    ]
    
    for filename, description in output_files:
        exists = os.path.exists(filename)
        if exists:
            size = os.path.getsize(filename)
            print_result(True, f"{filename} ({description}) - {size} bytes")
        else:
            print_result(False, f"{filename} ({description}) - 尚未生成 (需執行驗證)")
    
    return True  # 輸出檔案可能尚未生成，不視為失敗

# ============================================
# Main
# ============================================
def main():
    print("\n" + "="*60)
    print("  DQA Environmental Standard Checker - Validation Script")
    print("  Validating implementation against project_plan.md")
    print("="*60)
    
    # 切換到腳本所在目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    results = []
    results.append(("檔案結構", verify_file_structure()))
    results.append(("API 端點", verify_api_endpoint()))
    results.append(("爬蟲模組", verify_crawler_module()))
    results.append(("前端實作", verify_frontend()))
    results.append(("資料結構", verify_data_structure()))
    results.append(("輸出檔案", verify_output_files()))
    
    # 總結
    print_header("Validation Summary")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n  Passed: {passed}/{total} sections")
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"    {name}: {status}")
    
    if passed == total:
        print(f"\n[SUCCESS] All validations passed! Implementation matches project_plan.md.")
        return 0
    else:
        print(f"\n[WARNING] Some validations failed. Please check details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
