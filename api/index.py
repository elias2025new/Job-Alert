from http.server import BaseHTTPRequestHandler
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Path to index.html in the root directory
        # In Vercel, the root is usually the parent of the api/ directory
        path = os.path.join(os.path.dirname(__file__), '..', 'index.html')
        
        try:
            with open(path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error loading dashboard: {str(e)}".encode())
