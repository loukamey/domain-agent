import requests
from bs4 import BeautifulSoup
import schedule
import time
from datetime import datetime
import json
import os
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = "8982283074:AAGt48KiXFQaBjDM-mOIZJf6BjlCjvZRIdQ"
TELEGRAM_CHAT_ID = "8526660731"
GODADDY_KEY = "hkTZnBsatcP5_5pdqfYUZ62PyBL7ZSFsQE7"
GODADDY_SECRET = "PqsePsSV1rYMXnaYbPSYst"

TRENDING_KEYWORDS = [
    "dubai", "uae", "ai", "crypto", "luxury", "gold", "invest",
    "agent", "hub", "app", "pro", "smart", "fast", "easy", "now"
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

def check_available(domain):
    try:
        headers = {"Authorization": f"sso-key {GODADDY_KEY}:{GODADDY_SECRET}"}
        url = f"https://api.godaddy.com/v1/domains/available?domain={domain}&checkType=FAST"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        available = data.get("available", False)
        price = data.get("price", 0)
        return available, price
    except Exception as e:
        print(f"Check error for {domain}: {e}")
        return False, 0

def get_available_suggestions():
    available_domains = []
    try:
        headers = {"Authorization": f"sso-key {GODADDY_KEY}:{GODADDY_SECRET}"}
        
        trending_combos = [
            "dubai", "uae", "dubaiAI", "UAEtech", "dubailuxury",
            "AIagent", "AIcoach", "AImentor", "AIdubai", "AIinvest",
            "cryptodubai", "dubaicrypto", "goldtoken", "smartinvest",
            "dubaipropertyAI", "UAEinvest", "gulfinvest", "gulfAI"
        ]
        
        for query in trending_combos[:8]:
            url = f"https://api.godaddy.com/v1/domains/suggest?query={query}&country=AE&city=Dubai&limit=3&tlds=com"
            r = requests.get(url, headers=headers, timeout=10)
            suggestions = r.json()
            
            for s in suggestions:
                domain = s.get("domain", "")
                if domain and domain.endswith(".com"):
                    available, price = check_available(domain)
                    if available:
                        available_domains.append({
                            "domain": domain,
                            "price_usd": round(price / 1000000, 2) if price > 1000 else 12,
                            "available": True,
                            "verified": True
                        })
                        print(f"AVAILABLE: {domain}")
                        
        print(f"Found {len(available_domains)} verified available domains")
    except Exception as e:
        print(f"Suggestions error: {e}")
    return available_domains[:10]

def generate_report(domains):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are Louka's domain flipping advisor. Louka is 18, lives in Dubai, budget 500 AED.

Today: {datetime.now().strftime("%B %d, %Y")}

IMPORTANT: These domains are 100% verified available to buy RIGHT NOW on Namecheap/GoDaddy:
{json.dumps(domains, indent=2)}

Every domain listed here CAN BE BOUGHT TODAY. Do not suggest anything else.

Hey Louka domain report for today:

🌐 TOP DOMAIN PICK
- [best domain from the list] — [why valuable, who buys it, realistic resale value]
- Buy now: ~$12 on Namecheap
- List for: $[X] on Afternic

💎 OTHER AVAILABLE TODAY
- [domain 2] — [one line why good]
- [domain 3] — [one line why good]

🚫 AVOID
- [what types to skip]

💡 TIP
- [one actionable tip]

👀 ACTION
- Go to Namecheap NOW and search [top domain] — it is available today"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def hourly_check():
    print(f"Hourly check - {datetime.now()}")
    domains = get_available_suggestions()
    urgent = [d for d in domains if any(k in d["domain"].lower() for k in ["dubai", "uae", "ai"]) and len(d["domain"].replace(".com","")) <= 10]
    if urgent:
        domain = urgent[0]["domain"]
        alert = f"🚨‼️ LOUKA — ACT NOW\n\n<b>{domain}</b> — premium domain available NOW.\n\n→ Search on namecheap.com — buy for ~$12\n\n⏰ {datetime.now().strftime('%H:%M')} Dubai time"
        send_telegram(alert)

def daily_job():
    print(f"Running domain scan - {datetime.now()}")
    domains = get_available_suggestions()
    print(f"Found {len(domains)} verified available domains")
    if domains:
        report = generate_report(domains)
    else:
        report = "No premium available domains found today. Check back tomorrow — the agent scans fresh every day."
    send_telegram(f"🌐 <b>Your Daily Domain Report - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}")

print("Domain Agent running!")
print(f"Started: {datetime.now()}")
daily_job()

schedule.every().day.at("07:00").do(daily_job)
schedule.every(1).hours.do(hourly_check)

while True:
    schedule.run_pending()
    time.sleep(60)
