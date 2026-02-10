import http.server
import socketserver
import webbrowser
import os
import subprocess
import json

PORT = 8001

class DQAHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/run-verify':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                # Run the verification script with real-time output to console
                print("Running verify_standards.py...")
                print("-" * 50)
                # Don't capture output - let it flow to the console directly
                result = subprocess.run(
                    ['python', '-u', 'verify_standards.py'],  # -u for unbuffered output
                    text=True
                )
                print("-" * 50)
                
                if result.returncode == 0:
                    response = {'status': 'success', 'message': 'Verification complete'}
                else:
                    response = {'status': 'error', 'message': 'Script failed'}
                    
            except Exception as e:
                response = {'status': 'error', 'message': str(e)}
                
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/api/sync-data':
            # Sync updated standards from localStorage back to data.js
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                standards = json.loads(post_data.decode('utf-8'))
                
                # Format as data.js file content
                js_content = "console.log('Data.js loading...');\n"
                js_content += "window.initialStandards = "
                js_content += json.dumps(standards, indent=4, ensure_ascii=False)
                js_content += ";\n"
                
                # Write to data.js
                with open('data.js', 'w', encoding='utf-8') as f:
                    f.write(js_content)
                
                print(f"[SYNC] Updated data.js with {len(standards)} standards")
                response = {'status': 'success', 'message': f'Synced {len(standards)} standards to data.js'}
                
            except Exception as e:
                print(f"[SYNC ERROR] {str(e)}")
                response = {'status': 'error', 'message': str(e)}
                
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

print(f"Starting DQA Server at http://localhost:{PORT}")
print("--------------------------------------------------")
print("  Server is RUNNING. Please KEEP THIS WINDOW OPEN.")
print("  You can minimize this window, but do not close it.")
print("--------------------------------------------------")
print("Press Ctrl+C to stop.")

# Auto-open browser
webbrowser.open(f'http://localhost:{PORT}')

with socketserver.TCPServer(("", PORT), DQAHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
