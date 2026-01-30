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
    
    # DDG HTML structure: .result -> .result__title -> a (href, text)
    # .result__snippet (body)
    
    for result in soup.find_all('div', class_='result'):
        try:
            title_tag = result.find('a', class_='result__a')
            if not title_tag:
                continue
                
            title = title_tag.get_text(strip=True)
            link = title_tag['href']
            
            snippet_tag = result.find('a', class_='result__snippet')
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            
            results.append({
                "title": title,
                "link": link,
                "source": snippet
            })
            
            # Limit to top 5 per query
            if len(results) >= 5:
                break
        except Exception:
            continue
            
    # Sleep briefly to be nice to the server
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

    print(f"Sending Telegram alert for {len(jobs)} jobs...")
    
    if not jobs:
        message = "No new jobs found today."
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        return

    header = f"🚀 **Daily Job Alert: {datetime.now().strftime('%Y-%m-%d')}**\n\n"
    
    # Send in chunks
    current_message = header
    count = 0
    # Deduplicate by link
    seen_links = set()
    
    for job in jobs:
        if job['link'] in seen_links:
            continue
        seen_links.add(job['link'])
        
        if count >= 15: # Max 15 unique jobs to avoid spam
            break
            
        line = f"🔹 [{job['title']}]({job['link']})\n"
        if len(current_message) + len(line) > 4000:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                          json={"chat_id": TELEGRAM_CHAT_ID, "text": current_message, "parse_mode": "Markdown"})
            current_message = ""
        current_message += line
        count += 1

    if current_message:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": current_message, "parse_mode": "Markdown"})

def send_email_alert(jobs):
    if not EMAIL_USER or not EMAIL_PASS:
        print("Email secrets not found. Skipping Email.")
        return

    print("Sending Email alert...")
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER 
    msg['Subject'] = f"Daily Job Alert - {datetime.now().strftime('%Y-%m-%d')}"

    if not jobs:
        body = "No new jobs found today."
    else:
        body = "<h3>Top Job Picks</h3><ul>"
        seen_links = set()
        count = 0
        for job in jobs:
            if job['link'] in seen_links:
                continue
            seen_links.add(job['link'])
            
            if count >= 30: # Max 30 for email
                break
                
            body += f"<li><a href='{job['link']}'><b>{job['title']}</b></a><br>{job['source']}</li>"
            count += 1
        body += "</ul>"

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
