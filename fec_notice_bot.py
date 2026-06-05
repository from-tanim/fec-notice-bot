import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

import os

BOT_TOKEN = os.environ.get('7759430951:AAEar9Ld2dqKEjC_Kn__HdMYAfQogQ_HGiM')
CHAT_ID = os.environ.get('5814642141')

# ========== CONFIGURATION ==========
# REPLACE THESE WITH YOUR ACTUAL VALUES!
BOT_TOKEN = "7759430951:AAEar9Ld2dqKEjC_Kn__HdMYAfQogQ_HGiM"  # Paste your bot token here
CHAT_ID = "5814642141"      # Paste your chat ID here
NOTICE_URL = "https://fec.ac.bd/pages/notices"

# File to store already sent notices
DATA_FILE = "sent_notices.json"

def get_pdf_link(notice_row):
    """Extract PDF link from the notice row"""
    try:
        # The "দেখুন" (View) button is in the 3rd column (index 2)
        files_cell = notice_row.find_all('td')[2]
        view_link = files_cell.find('a', text='দেখুন')
        
        if view_link and view_link.get('href'):
            pdf_url = view_link['href']
            # Convert relative URL to absolute URL
            if pdf_url.startswith('/'):
                pdf_url = 'https://fec.ac.bd' + pdf_url
            return pdf_url
        return None
    except Exception as e:
        print(f"Error getting PDF link: {e}")
        return None

def get_notices():
    """Scrape all notices from the FEC website"""
    try:
        # Use a browser-like header to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Fetch the webpage
        response = requests.get(NOTICE_URL, headers=headers, timeout=10)
        response.raise_for_status()  # Raise error if request failed
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        notices = []
        
        # Find the notice table
        table = soup.find('table')
        if not table:
            print("Could not find table on page")
            return notices
        
        # Get all rows except the header row
        rows = table.find_all('tr')[1:]
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:  # Make sure row has enough columns
                # Extract notice number (column 0)
                notice_no = cols[0].get_text(strip=True)
                
                # Extract title (column 1)
                title = cols[1].get_text(strip=True)
                
                # Extract PDF link (column 2)
                pdf_link = get_pdf_link(row)
                
                # Extract date (column 4)
                date = cols[4].get_text(strip=True)
                
                # Only add if we have title and PDF link
                if title and pdf_link:
                    notices.append({
                        'no': notice_no,
                        'title': title,
                        'link': pdf_link,
                        'date': date,
                        'timestamp': datetime.now().isoformat()
                    })
        
        print(f"Found {len(notices)} notices")
        return notices
    except Exception as e:
        print(f"Error fetching notices: {e}")
        return []

def load_sent_notices():
    """Load previously sent notices from file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_sent_notices(notices):
    """Save sent notices to file"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(notices, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(notices)} notices to file")
    except Exception as e:
        print(f"Error saving notices: {e}")

def send_telegram_message(title, link, date, notice_no):
    """Send a message to Telegram using the bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Create beautiful message
    message = f"""📢 *NEW NOTICE ALERT!*

*Notice #{notice_no}*
📌 *Title:* {title}
📅 *Date:* {date}

🔗 *Download PDF:* [Click Here to Open]({link})

---
🤖 *FEC Notice Bot* - Automatic Notification System"""
    
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown',  # Allows bold text and links
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.ok:
            print(f"✓ Sent: {title}")
            return True
        else:
            print(f"✗ Failed: {title} - {response.text}")
            return False
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def check_for_new_notices():
    """Main function - checks for new notices and sends alerts"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new notices...")
    
    # Get current notices from website
    current_notices = get_notices()
    if not current_notices:
        print("No notices found or website is down")
        return
    
    # Load previously sent notices
    sent_notices = load_sent_notices()
    sent_links = {notice['link'] for notice in sent_notices}
    
    # Find new notices (not in sent list)
    new_notices = [n for n in current_notices if n['link'] not in sent_links]
    
    if new_notices:
        print(f"✨ Found {len(new_notices)} new notice(s)!")
        
        # Send each new notice
        for notice in new_notices:
            success = send_telegram_message(
                notice['title'],
                notice['link'],
                notice['date'],
                notice['no']
            )
            time.sleep(1)  # Delay to avoid rate limiting
        
        # Update sent notices list (keep last 100)
        all_notices = new_notices + sent_notices
        save_sent_notices(all_notices[:100])
    else:
        print("No new notices found")
    
    print("Check completed!")

# This is the entry point when the script runs
if __name__ == "__main__":
    print("🤖 FEC Notice Bot Starting...")
    print(f"Monitoring: {NOTICE_URL}")
    check_for_new_notices()
    print("Bot finished execution.")
