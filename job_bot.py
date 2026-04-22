import requests
from bs4 import BeautifulSoup
import json
import os

# --- Configuration ---
# Replace these with your actual bot token and chat ID
BOT_TOKEN = "8750208546:AAFZ_z3fQRSDpmr82lTszMRBb1GuuxOlPRc"
CHAT_ID = "5908397596"

TARGET_URL = "https://www.ethiopianskylighthotel.com/vacancies"
STATE_FILE = "state.json"

# List of keywords to search for (lowercase for case-insensitive matching)
KEYWORDS = [
    "it officer", 
    "information technology", 
    "it support", 
    "system administrator", 
    "network", 
    "ict"
]

# Headers to mimic a standard browser and avoid basic blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def load_state():
    """Loads the previously saved keywords from state.json."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error decoding state.json. Starting fresh.")
            return []
    return []

def save_state(matched_keywords):
    """Saves the matched keywords to state.json."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(matched_keywords, f)
    except IOError as e:
        print(f"Error saving to {STATE_FILE}: {e}")

def send_telegram_message(matched_keywords):
    """Sends a markdown-formatted message to Telegram."""
    if not BOT_TOKEN or BOT_TOKEN == "<YOUR_BOT_TOKEN>":
        print("Telegram BOT_TOKEN is not configured. Skipping message.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Format the message using Markdown
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
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")

def scrape_jobs():
    """Main function to scrape the page and process keywords."""
    print(f"Fetching data from {TARGET_URL}...")
    
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return

    print("Page fetched successfully. Parsing content...")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract all text from the page and convert to lowercase for easy matching
    page_text = soup.get_text(separator=' ', strip=True).lower()

    print("Checking for keywords...")
    found_keywords = []
    for keyword in KEYWORDS:
        if keyword in page_text:
            found_keywords.append(keyword)

    previous_keywords = load_state()

    if found_keywords:
        print(f"Found keywords: {found_keywords}")
        
        # Sort lists to ensure [a, b] equals [b, a] when comparing
        if sorted(found_keywords) != sorted(previous_keywords):
            print("New keywords found! Sending notification...")
            send_telegram_message(found_keywords)
            save_state(found_keywords)
        else:
            print("Keywords found, but they are exactly the same as the last run. No notification sent.")
    else:
        print("No IT-related keywords found on the page.")
        # If no keywords found, but state had previous keywords, clear it
        if previous_keywords:
            print("Clearing saved state.")
            save_state([])
            
    print("Job monitoring run complete.")

if __name__ == "__main__":
    scrape_jobs()
