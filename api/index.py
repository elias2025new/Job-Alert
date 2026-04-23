from http.server import BaseHTTPRequestHandler
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Determine which file to serve based on the path
        current_dir = os.path.dirname(__file__)
        if self.path == '/' or self.path == '/index.html':
            file_path = os.path.join(current_dir, 'index.html')
            content_type = 'text/html'
        elif self.path == '/style.css':
            file_path = os.path.join(current_dir, 'style.css')
            content_type = 'text/css'
        elif self.path == '/script.js':
            file_path = os.path.join(current_dir, 'script.js')
            content_type = 'application/javascript'
        else:
            self.send_response(404)
            self.end_headers()
            return

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error loading {self.path}: {str(e)}".encode())
