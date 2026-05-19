import requests
import schedule
import time
from datetime import datetime
import json
import os
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = "8982283074:AAGt48KiXFQaBjDM-mOIZJf6BjlCjvZRIdQ"
TELEGRAM_CHAT_ID = "8526660731"

VALUABLE_KEYWORDS = [
    "dubai", "uae", "luxury", "crypto", "gold", "invest", "realestate",
    "tech", "ai", "nft", "trade", "finance", "villa", "resort", "hotel",
    "shop", "store", "market", "buy", "sell", "deal", "premium", "elite"
]

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
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                for row in soup.select("table.base1 tr")[:5]:
                    cols = row.find_all("td")
                    if cols and len(cols) > 1:
                        domain = cols[0].text.strip()
                        if domain and "." in domain:
                            domains.append({
                                "domain": domain,
                                "keyword": keyword,
                                "date": datetime.now().strftime("%Y-%m-%d")
                            })
    except Exception as e:
        print(f"Domain scraper error: {e}")
    return domains

def generate_report(domains):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are Louka's personal domain flipping advisor. Louka is 13, lives in Dubai, has a budget of 500 AED for domains. Each domain costs $10-15 to register.

Today: {datetime.now().strftime("%B %d, %Y")}
Expiring domains found: {json.dumps(domains, indent=2)}

Write his daily domain brief in this EXACT bullet point format:

Hey Louka 👋 Domain report for today:

🌐 TOP DOMAIN PICK
- [domain.com] — [why it's valuable, who would buy it, estimated resale value]
- Buy it for: ~$12 (44 AED)
- Sell it for: $[X] - $[X] on Sedo.com

💎 OTHER GOOD FINDS
- [domain.com] — [one line why it's good]
- [domain.com] — [one line why it's good]

🚫 AVOID
- [type of domains to avoid today and why]

💡 DOMAIN TIP OF THE DAY
- [One practical tip about domain flipping]

👀 WHAT TO DO
- [Exact next step Louka should take today]

If no good domains found today, give general domain flipping advice and what keywords to watch."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def daily_job():
    print(f"Running domain scan - {datetime.now()}")
    domains = find_expiring_domains()
    print(f"Found {len(domains)} domains")
    report = generate_report(domains)
    message = f"🌐 <b>Your Daily Domain Report - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}"
    send_telegram(message)

print("Domain Flipping Agent is running!")
print(f"Started at: {datetime.now()}")
print("Sending domain report now...")
daily_job()

schedule.every().day.at("07:00").do(daily_job)

while True:
    schedule.run_pending()
    time.sleep(60)
