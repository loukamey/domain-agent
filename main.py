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

VALUABLE_KEYWORDS = ["dubai", "uae", "luxury", "crypto", "gold", "invest", "realestate", "tech", "ai", "nft", "trade", "finance", "villa", "resort", "hotel"]
PREMIUM_KEYWORDS = ["dubai", "uae", "ai", "crypto", "luxury", "gold"]

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("Telegram message sent!")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

def find_expiring_domains():
    domains = []
    try:
        for keyword in VALUABLE_KEYWORDS[:5]:
            url = f"https://expireddomains.net/domain-name-search/?q={keyword}&ftlds[]=com&fwhois[]=22&start=0"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for row in soup.select("table.base1 tr")[:5]:
                    cols = row.find_all("td")
                    if cols and len(cols) > 1:
                        domain = cols[0].text.strip()
                        if domain and "." in domain:
                            is_premium = any(pk in domain.lower() for pk in PREMIUM_KEYWORDS)
                            is_short = len(domain.replace(".com", "")) <= 6
                            domains.append({
                                "domain": domain,
                                "premium": is_premium,
                                "short": is_short,
                            })
    except Exception as e:
        print(f"Domain error: {e}")
    return domains

def check_urgent(domains):
    urgent = []
    for d in domains:
        if d.get("premium") and d.get("short"):
            urgent.append(d["domain"])
    return urgent

def generate_report(domains):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are Louka's domain flipping advisor. 13, Dubai, 500 AED budget.

Today: {datetime.now().strftime("%B %d, %Y")}
Domains: {json.dumps(domains, indent=2)}

Hey Louka 👋 Domain report for today:

🌐 TOP DOMAIN PICK
- [domain.com] — [why valuable, who buys, resale value]
- Buy: ~$12 (44 AED) on Namecheap
- Sell: $[X]-$[X] on Afternic

💎 OTHER GOOD FINDS
- [domain] — [one line]
- [domain] — [one line]

🚫 AVOID
- [what to avoid and why]

💡 TIP OF THE DAY
- [One practical tip]

👀 WHAT TO DO TODAY
- [Exact next step]"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def hourly_check():
    print(f"Hourly domain check - {datetime.now()}")
    domains = find_expiring_domains()
    urgent = check_urgent(domains)
    if urgent:
        domain = urgent[0]
        alert = f"🚨🔴🚨🔴🚨🔴🚨🔴🚨\n\n<b>LOUKA — ACT NOW</b>\n\n<b>{domain}</b> — premium short domain expiring NOW. Could sell for $500-2,000+.\n\n→ namecheap.com — buy for ~$12\n\n⏰ {datetime.now().strftime('%H:%M')} Dubai time"
        send_telegram(alert)
        print("URGENT DOMAIN ALERT SENT")

def daily_job():
    print(f"Running domain scan - {datetime.now()}")
    domains = find_expiring_domains()
    report = generate_report(domains)
    message = f"🌐 <b>Your Daily Domain Report - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}"
    send_telegram(message)

print("Domain Agent running!")
print(f"Started: {datetime.now()}")
daily_job()

schedule.every().day.at("07:00").do(daily_job)
schedule.every(1).hours.do(hourly_check)

while True:
    schedule.run_pending()
    time.sleep(60)
