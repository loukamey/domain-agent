import requests
import socket
import schedule
import time
from datetime import datetime
import json
import os
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = "8982283074:AAGt48KiXFQaBjDM-mOIZJf6BjlCjvZRIdQ"
TELEGRAM_CHAT_ID = "8526660731"

TRENDING_DOMAINS_TO_CHECK = [
    "dubaiai.pro", "gulfaiagent.com", "aimenordubai.com",
    "dubaiwebai.com", "uaefintech.pro", "aicoachuae.com",
    "dubaicryptobot.com", "smartdubaiapp.com", "uaetradingai.com",
    "dubaiblockchain.pro", "aistartupuae.com", "dubaidefiapp.com",
    "uaeluxuryai.com", "gulfproptech.com", "dubaiaicoach.com",
    "uaecryptobot.com", "aidubaiwealth.com", "gulfsmartinvest.com",
    "dubaitechpro.com", "uaeaimentor.com", "gulfaimentor.com",
    "dubaiaitrader.com", "uaewealthbot.com", "gulfcryptoai.com",
    "dubaismarthome.pro", "uaeproptechAI.com", "airealestateuae.com"
]

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("Telegram message sent!")
    except Exception as e:
        print(f"Telegram error: {e}")

def check_domain_available(domain):
    try:
        url = f"https://api.domainsdb.info/v1/domains/search?domain={domain}&zone=com"
        r = requests.get(url, timeout=10)
        data = r.json()
        found = len(data.get("domains", [])) > 0
        return not found
    except:
        try:
            socket.gethostbyname(domain)
            return False
        except socket.gaierror:
            return True

def find_available_domains():
    available = []
    print(f"Checking {len(TRENDING_DOMAINS_TO_CHECK)} domains...")
    for domain in TRENDING_DOMAINS_TO_CHECK:
        is_available = check_domain_available(domain)
        if is_available:
            available.append({
                "domain": domain,
                "available": True,
                "price_usd": 12,
                "verified_today": datetime.now().strftime("%Y-%m-%d")
            })
            print(f"AVAILABLE: {domain}")
        else:
            print(f"Taken: {domain}")
    return available

def generate_report(domains):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are Louka's domain flipping advisor. Louka is 18, lives in Dubai, budget 500 AED.

Today: {datetime.now().strftime("%B %d, %Y")}

These domains are VERIFIED AVAILABLE TO BUY RIGHT NOW today:
{json.dumps(domains, indent=2)}

Hey Louka domain report for today:

🌐 TOP DOMAIN PICK
- [best domain] — [why valuable, who would buy it, realistic resale $]
- Buy now: ~$12 on Namecheap
- List for: $[X] on Afternic

💎 OTHER AVAILABLE TODAY
- [domain 2] — [one line why]
- [domain 3] — [one line why]

🚫 AVOID
- [what types to skip]

💡 TIP
- [one actionable tip for today]

👀 ACTION
- Go buy [top domain] on Namecheap right now — verified available today"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def daily_job():
    print(f"Running domain scan - {datetime.now()}")
    domains = find_available_domains()
    print(f"Found {len(domains)} available domains")
    if domains:
        report = generate_report(domains)
    else:
        report = "All monitored domains taken today. New list checked tomorrow."
    send_telegram(f"🌐 <b>Your Daily Domain Report - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}")

def hourly_check():
    print(f"Hourly check - {datetime.now()}")

print("Domain Agent running!")
print(f"Started: {datetime.now()}")
daily_job()

schedule.every().day.at("07:00").do(daily_job)
schedule.every(1).hours.do(hourly_check)

while True:
    schedule.run_pending()
    time.sleep(60)
