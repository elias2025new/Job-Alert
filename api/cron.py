from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import os
import json

try:
    from supabase import create_client, Client
except ImportError:
    pass

# --- Configuration ---
# We use environment variables so we don't hardcode secrets in GitHub!
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

TARGET_URL = "https://www.ethiopianskylighthotel.com/vacancies"

# List of keywords to search for (lowercase for case-insensitive matching)
KEYWORDS = [
    "it officer", 
    "information technology", 
    "it support", 
    "system administrator", 
    "network", 
    "ict"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def load_state():
    """Loads the previously saved keywords from Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase credentials missing. Skipping state load.")
        return []
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("job_state").select("keywords").eq("id", 1).execute()
        if response.data:
            return response.data[0].get("keywords", [])
    except Exception as e:
        print(f"Error loading state from Supabase: {e}")
    return []

def save_state(matched_keywords):
    """Saves the matched keywords to Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase credentials missing. Skipping state save.")
        return
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Upsert updates the row if id=1 exists, or inserts if it doesn't
        supabase.table("job_state").upsert({"id": 1, "keywords": matched_keywords}).execute()
    except Exception as e:
        print(f"Error saving state to Supabase: {e}")

def send_telegram_message(matched_keywords):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram credentials missing in Vercel Environment Variables.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    keywords_str = ", ".join([f"`{kw}`" for kw in matched_keywords])
    message = (
        f"🚨 *New IT Job(s) Detected!* 🚨\n\n"
        f"*Matched Keywords:* {keywords_str}\n"
        f"*Check here:* [Ethiopian Skylight Hotel Vacancies]({TARGET_URL})"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Telegram notification sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        return False

def scrape_jobs():
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return False

    soup = BeautifulSoup(response.text, 'html.parser')
    page_text = soup.get_text(separator=' ', strip=True).lower()

    found_keywords = [kw for kw in KEYWORDS if kw in page_text]
    previous_keywords = load_state()

    if found_keywords:
        print(f"Found keywords: {found_keywords}")
        
        if sorted(found_keywords) != sorted(previous_keywords):
            print("New keywords found! Sending notification...")
            send_telegram_message(found_keywords)
            save_state(found_keywords)
            return True
        else:
            print("Keywords found, but exactly the same as last time. No notification sent.")
            return False
    else:
        print("No IT jobs found.")
        if previous_keywords:
            print("Clearing saved state.")
            save_state([])
        return False

# Vercel Serverless Function Handler
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        job_found = scrape_jobs()
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        if job_found:
            self.wfile.write(b"Scrape completed: Jobs found and alert sent.")
        else:
            self.wfile.write(b"Scrape completed: No new jobs found.")
