import os
import smtplib
import time
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime

# --- Configuration ---
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Keywords to search
KEYWORDS = [
    "Software Engineer Intern 2026",
    "Off-campus drive 2026 fresher",
    "Software Developer freshers hiring",
    "Summer Internship 2026 India",
    "Entry level software engineer remote"
]

import urllib.parse
# ... (existing imports)

# ... (keyword config)

def get_ddg_results(query):
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    url = "https://html.duckduckgo.com/html/"
    payload = {'q': query}
    
    print(f"Querying: {query}")
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {query}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    
    for result in soup.find_all('div', class_='result'):
        try:
            title_tag = result.find('a', class_='result__a')
            if not title_tag:
                continue
                
            title = title_tag.get_text(strip=True)
            raw_link = title_tag['href']
            
            # Decode DDG redirect to get real link
            # Format: /l/?uddg=REAL_URL&rut=...
            if "uddg=" in raw_link:
                parsed = urllib.parse.urlparse(raw_link)
                qs = urllib.parse.parse_qs(parsed.query)
                link = qs.get('uddg', [raw_link])[0]
            else:
                link = raw_link
            
            snippet_tag = result.find('a', class_='result__snippet')
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            
            results.append({
                "title": title,
                "link": link,
                "source": snippet
            })
            
            if len(results) >= 5:
                break
        except Exception:
            continue
            
    time.sleep(1) 
    return results

def search_jobs():
    print("Searching for jobs via Custom Scraper...")
    all_jobs = []
    for query in KEYWORDS:
        jobs = get_ddg_results(query)
        all_jobs.extend(jobs)
    return all_jobs

def send_telegram_alert(jobs):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram secrets not found. Skipping Telegram.")
        return

    # Debug: Print masked secrets to confirm they are loaded (DO NOT PRINT FULL SECRETS)
    print(f"Debug: Bot Token loaded? {'Yes' if TELEGRAM_BOT_TOKEN else 'No'}")
    print(f"Debug: Chat ID loaded? {'Yes' if TELEGRAM_CHAT_ID else 'No'}")
    print(f"Debug: Sending to Chat ID: {TELEGRAM_CHAT_ID} (Verify this matches your user ID)")

    print(f"Sending Telegram alert for {len(jobs)} jobs...")
    
    if not jobs:
        return

    # Send a header message first
    header_msg = f"🔍 **Job Search Update**\n📅 {datetime.now().strftime('%d %b %Y %H:%M')}\nFound {len(jobs)} potential roles."
    try:
        resp = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  json={"chat_id": TELEGRAM_CHAT_ID, "text": header_msg, "parse_mode": "Markdown"})
        print(f"Telegram Header Status: {resp.status_code}")
        print(f"Telegram Header Response: {resp.text}") # Print full response for debugging
    except Exception as e:
        print(f"Telegram Exception: {e}")

    # Send individual messages for top jobs
    seen_links = set()
    count = 0
    
    for job in jobs:
        if job['link'] in seen_links:
            continue
        seen_links.add(job['link'])
        
        if count >= 10: 
            break
            
        msg = (
            f"💼 **{job['title']}**\n\n"
            f"🔗 [Tap to Apply]({job['link']})\n\n"
            f"📝 *Source snippet*: {job['source'][:200]}..."
        )
        
        try:
            resp = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True})
            if resp.status_code != 200:
                print(f"Telegram Job {count} Error: {resp.text}")
        except Exception as e:
            print(f"Telegram Job {count} Exception: {e}")
        
        count += 1
        time.sleep(1)

def send_email_alert(jobs):
    if not EMAIL_USER or not EMAIL_PASS:
        print("Email secrets not found. Skipping Email.")
        return

    print("Sending Email alert...")
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER 
    msg['Subject'] = f"🚀 Daily Job Alert - {datetime.now().strftime('%Y-%m-%d')}"

    if not jobs:
        body = "<p>No new jobs found today.</p>"
    else:
        # Professional HTML Template
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px;">
                <h2 style="color: #2c3e50; margin: 0;">🚀 Daily Job Alert</h2>
                <p style="color: #7f8c8d;">{datetime.now().strftime('%d %b %Y')}</p>
            </div>
            <div style="padding: 20px;">
        """
        
        seen_links = set()
        count = 0
        for job in jobs:
            if job['link'] in seen_links:
                continue
            seen_links.add(job['link'])
            
            if count >= 30: # Max 30 for email
                break
            
            # Job Card
            body += f"""
            <div style="margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee;">
                <h3 style="margin: 0 0 10px; color: #2980b9;">{job['title']}</h3>
                <p style="margin: 0 0 10px; font-size: 14px; color: #555;">{job['source'][:300]}...</p>
                <a href="{job['link']}" style="display: inline-block; background-color: #3498db; color: #ffffff; padding: 10px 15px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px;">Apply Now ➝</a>
            </div>
            """
            count += 1
            
        body += """
            </div>
            <div style="text-align: center; padding: 20px; font-size: 12px; color: #aaa;">
                <p>Automated by GitHub Actions • Job Scraper Bot</p>
            </div>
        </body>
        </html>
        """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    found_jobs = search_jobs()
    print(f"Found {len(found_jobs)} jobs.")
    
    if found_jobs:
        send_telegram_alert(found_jobs)
        send_email_alert(found_jobs)
    else:
        print("No jobs found.")
