# -*- coding: utf-8 -*-
"""
DQA Environmental Standard Checker - 啟動器
此檔案用於 PyInstaller 打包，整合伺服器與瀏覽器啟動功能
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import threading
import time
import io
import verify_standards

# 設定 PORT
PORT = 8001

# 設定輸出編碼為 UTF-8，避免 cp950 編碼問題
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def get_resource_path(relative_path):
    """
    取得資源檔案的絕對路徑
    支援 PyInstaller 打包後的臨時目錄
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包後的臨時目錄
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_base_path():
    """取得基礎路徑（exe 所在目錄或腳本目錄）"""
    if hasattr(sys, '_MEIPASS'):
        # 打包後，使用 exe 所在目錄
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

class DQAHandler(http.server.SimpleHTTPRequestHandler):
    """自訂 HTTP 請求處理器"""
    
    def __init__(self, *args, **kwargs):
        # 設定靜態檔案目錄
        directory = get_resource_path(".")
        super().__init__(*args, directory=directory, **kwargs)
    
    def do_GET(self):
        """處理 GET 請求，優先從 exe 目錄讀取動態檔案"""
        # 需要從 exe 目錄讀取的檔案清單
        dynamic_files = ['data.js', 'verification_results.json']
        
        # 移除 query string
        clean_path = self.path.split('?')[0].lstrip('/')
        
        print(f"[DEBUG] Request: {self.path}, Clean: {clean_path}")
        
        if clean_path in dynamic_files:
            base_path = get_base_path()
            file_path = os.path.join(base_path, clean_path)
            print(f"[DEBUG] Looking for {clean_path} in {base_path} -> {file_path}")
            print(f"[DEBUG] Exists: {os.path.exists(file_path)}")
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    if clean_path.endswith('.js'):
                        self.send_header("Content-type", "application/javascript")
                    elif clean_path.endswith('.json'):
                        self.send_header("Content-type", "application/json")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    print(f"Error serving {clean_path}: {e}")
        
        # 預設行為（從資源目錄服務靜態檔案）
        super().do_GET()

    def do_POST(self):
        if self.path == '/api/run-verify':
            self.handle_verify()
        elif self.path == '/api/sync-data':
            self.handle_sync_data()
        else:
            self.send_error(404)
    
    def handle_verify(self):
        """處理驗證請求"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            base_path = get_base_path()
            print(f"開始驗證... (Base path: {base_path})")
            
            # 使用 verify_standards 模組執行驗證
            # 這會自動下載 ChromeDriver 並執行 Selenium
            result = verify_standards.run_verification(base_path)
            
            response = result
                    
        except Exception as e:
            print(f"驗證發生錯誤: {e}")
            response = {'status': 'error', 'message': str(e)}
            
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_sync_data(self):
        """處理資料同步請求"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            standards = json.loads(post_data.decode('utf-8'))
            
            # 寫入到 exe 目錄下的 data.js
            base_path = get_base_path()
            data_file = os.path.join(base_path, 'data.js')
            
            js_content = "console.log('Data.js loading...');\n"
            js_content += "window.initialStandards = "
            js_content += json.dumps(standards, indent=4, ensure_ascii=False)
            js_content += ";\n"
            
            with open(data_file, 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            print(f"[SYNC] Updated data.js with {len(standards)} standards")
            response = {'status': 'success', 'message': f'已同步 {len(standards)} 筆法規到 data.js'}
            
        except Exception as e:
            print(f"[SYNC ERROR] {str(e)}")
            response = {'status': 'error', 'message': str(e)}
            
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """自訂日誌格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def open_browser_delayed():
    """延遲開啟瀏覽器"""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{PORT}')


def main():
    """主程式入口"""
    print("=" * 60)
    print("  DQA Environmental Standard Checker")
    print("  [Law Standard Checker System]")
    print("=" * 60)
    
    # 初始化：確保 data.js 存在於 exe 目錄
    base_path = get_base_path()
    data_path = os.path.join(base_path, 'data.js')
    
    if not os.path.exists(data_path):
        try:
            resource_data = os.path.join(get_resource_path("."), 'data.js')
            if os.path.exists(resource_data):
                with open(resource_data, 'r', encoding='utf-8') as src:
                    content = src.read()
                with open(data_path, 'w', encoding='utf-8') as dst:
                    dst.write(content)
                print(f"Initialized data.js in {base_path}")
        except Exception as e:
            print(f"Failed to initialize data.js: {e}")

    print()
    print(f"  Server URL: http://localhost:{PORT}")
    print("  Press Ctrl+C to stop the server")
    print()
    print("=" * 60)
    
    # 在背景執行緒中開啟瀏覽器
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    # 啟動 HTTP 伺服器
    with socketserver.TCPServer(("", PORT), DQAHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
