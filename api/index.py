from http.server import BaseHTTPRequestHandler
import os
import json
import requests
from bs4 import BeautifulSoup

try:
    from supabase import create_client, Client
except ImportError:
    pass

# --- Configuration ---
TARGET_URL = "https://www.ethiopianskylighthotel.com/vacancies"
KEYWORDS = ["it officer", "information technology", "it support", "system administrator", "network", "ict"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# --- Helper Functions ---
def load_state():
    if not SUPABASE_URL or not SUPABASE_KEY: return []
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("job_state").select("keywords").eq("id", 1).execute()
        return response.data[0].get("keywords", []) if response.data else []
    except: return []

def save_state(matched_keywords):
    if not SUPABASE_URL or not SUPABASE_KEY: return
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table("job_state").upsert({"id": 1, "keywords": matched_keywords}).execute()
    except: pass

def send_telegram_message(matched_keywords):
    if not BOT_TOKEN or not CHAT_ID: return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    keywords_str = ", ".join([f"`{kw}`" for kw in matched_keywords])
    message = f"🚨 *Manual Scan: New IT Job(s) Detected!* 🚨\n\n*Matched Keywords:* {keywords_str}\n*Check here:* [Vacancies]({TARGET_URL})"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
        return True
    except: return False

def scrape_jobs():
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except: return {"success": False, "error": "Failed to fetch URL"}

    soup = BeautifulSoup(response.text, 'html.parser')
    page_text = soup.get_text(separator=' ', strip=True).lower()
    found_keywords = [kw for kw in KEYWORDS if kw in page_text]
    previous_keywords = load_state()

    new_found = False
    if found_keywords:
        if sorted(found_keywords) != sorted(previous_keywords):
            send_telegram_message(found_keywords)
            save_state(found_keywords)
            new_found = True
    elif previous_keywords:
        save_state([])

    return {
        "success": True,
        "found_keywords": found_keywords,
        "new_alert_sent": new_found,
        "previous_keywords": previous_keywords
    }

# --- Main Handler ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        current_dir = os.path.dirname(__file__)
        
        # Route: API Data
        if self.path == '/api/data':
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
            return

        # Route: Dashboard Assets
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
            self.wfile.write(f"Error loading asset: {str(e)}".encode())

    def do_POST(self):
        # Route: Trigger Scan
        if self.path == '/api/run':
            result = scrape_jobs()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            return
        
        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
