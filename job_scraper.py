import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from duckduckgo_search import DDGS
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
    "Summer Internship 2026 India",  # Adjusted for likely region based on requests
    "Entry level software engineer remote"
]

def search_jobs():
    print("Searching for jobs...")
    jobs = []
    with DDGS() as ddgs:
        for query in KEYWORDS:
            print(f"Querying: {query}")
            # 'd' parameter filters for results from the past day
            results = list(ddgs.text(f"{query}", region='in-en', timelimit='d', max_results=5))
            for r in results:
                jobs.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "source": r.get("body")
                })
    return jobs

def send_telegram_alert(jobs):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram secrets not found. Skipping Telegram.")
        return

    print("Sending Telegram alert...")
    
    # Telegram sends concise messages. We'll send one message per interesting job or a summary.
    # To avoid spamming, let's send a summary.
    
    if not jobs:
        message = "No new jobs found today."
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        return

    header = f"🚀 **Daily Job Alert: {datetime.now().strftime('%Y-%m-%d')}**\n\n"
    
    # Send in chunks if getting too long
    current_message = header
    for job in jobs[:10]: # Limit to top 10 to avoid spamming too much in one go
        line = f"🔹 [{job['title']}]({job['link']})\n"
        if len(current_message) + len(line) > 4000:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                          json={"chat_id": TELEGRAM_CHAT_ID, "text": current_message, "parse_mode": "Markdown"})
            current_message = ""
        current_message += line

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
    msg['To'] = EMAIL_USER # Send to self
    msg['Subject'] = f"Daily Job Alert - {datetime.now().strftime('%Y-%m-%d')}"

    if not jobs:
        body = "No new jobs found today."
    else:
        body = "<h3>Top Job Picks Today</h3><ul>"
        for job in jobs:
            body += f"<li><a href='{job['link']}'><b>{job['title']}</b></a><br>{job['source']}</li>"
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
        print("No jobs found, checking if we should alert anyway.")
