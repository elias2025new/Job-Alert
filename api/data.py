from http.server import BaseHTTPRequestHandler
import os
import json
try:
    from supabase import create_client, Client
except ImportError:
    pass

# Configuration (mirrored from cron.py for consistency)
TARGET_URL = "https://www.ethiopianskylighthotel.com/vacancies"
KEYWORDS = [
    "it officer", 
    "information technology", 
    "it support", 
    "system administrator", 
    "network", 
    "ict"
]

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def load_state():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("job_state").select("keywords").eq("id", 1).execute()
        if response.data:
            return response.data[0].get("keywords", [])
    except Exception:
        pass
    return []

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        last_keywords = load_state()
        
        data = {
            "status": "online",
            "target_url": TARGET_URL,
            "keywords": KEYWORDS,
            "last_scan_result": last_keywords,
            "bot_active": True
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
