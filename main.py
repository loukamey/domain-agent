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
GODADDY_KEY = "3mM44YwfTALAHB_N34T2ixsfpPa6v8kGufv7f"
GODADDY_SECRET = "MLPFme9ScsrNoUrkJZnamF"

VALUABLE_KEYWORDS = ["dubai", "uae", "luxury", "crypto", "gold", "invest", "ai", "tech", "villa", "resort"]
PREMIUM_KEYWORDS = ["dubai", "uae", "ai", "crypto", "luxury", "gold"]

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("Telegram message sent!")
    except Exception as e:
        print(f"Telegram error: {e}")

def get_domain_suggestions():
    domains = []
    try:
        headers = {"Authorization": f"sso-key {GODADDY_KEY}:{GODADDY_SECRET}"}
        for keyword in PREMIUM_KEYWORDS[:3]:
            url = f"https://api.godaddy.com/v1/domains/suggest?query={keyword}&country=AE&limit=5"
            response = requests.get(url, headers=headers, timeout=10)
            for s in response.json():
                domain = s.get("domain", "")
                if domain:
                    domains.append({"domain": domain, "source": "GoDaddy", "premium": True})
    except Exception as e:
        print(f"GoDaddy error: {e}")
    return domains

def find_expiring_domains():
    domains = []
    try:
        for keyword in VALUABLE_KEYWORDS[:5]:
            url = f"https://expireddomains.net/domain-name-search/?q={keyword}&ftlds[]=com&fwhois[]=22&start=0"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for row in soup.select("table.base1 tr")[:5]:
                    cols = row.find_all("td")
                    if cols and len(cols) > 1:
                        domain = cols[0].text.strip()
                        if domain and "." in domain:
                            domains.append({"domain": domain, "source": "ExpiredDomains"})
    except Exception as e:
        print(f"ExpiredDomains error: {e}")
    return domains

def generate_report(domains, suggestions):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    all_domains = domains + suggestions
    prompt = f"""You are Louka's domain flipping advisor. Louka is 18, lives in Dubai, budget 500 AED.
Today: {datetime.now().strftime("%B %d, %Y")}
Expiring domains: {json.dumps(domains, indent=2)}
GoDaddy suggestions: {json.dumps(suggestions, indent=2)}

Hey Louka domain report for today:

TOP DOMAIN PICK
domain and why valuable, who buys, resale value
Buy around 12 dollars on Namecheap
Sell estimate on Afternic

OTHER GOOD FINDS
two more domains with one line each

AVOID
what to avoid and why

TIP OF THE DAY
one practical tip

WHAT TO DO TODAY
exact next step"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def daily_job():
    print(f"Running domain scan - {datetime.now()}")
    domains = find_expiring_domains()
    suggestions = get_domain_suggestions()
    print(f"Found {len(domains)} expiring + {len(suggestions)} suggestions")
    report = generate_report(domains, suggestions)
    send_telegram(f"Domain Report - {datetime.now().strftime('%B %d, %Y')}\n\n{report}")

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
