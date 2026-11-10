import json
import os
import re
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "9180642674:AAF3I1uvZjswB89NXhrCCju6AgGVt2iSg6s"
CHAT_ID = "5384901785"
DATA_FILE = "fiyatlar.json"

# ScraperAPI Anahtarı
SCRAPER_API_KEY = "48b2cb0a50971b43fd599eb90d82e8d0"

PRODUCTS = [
    {
        "id": "hb_s12_gri",
        "name": "Hepsiburada - Tab S12 Ultra (Gri)",
        "site": "hepsiburada",
        "url": "https://www.hepsiburada.com/samsung-galaxy-tab-s12-ultra-12gb-ram-256gb-depolama-alani-14-6-inc-120hz-ekran-wifi7-s-pen-dahil-gri-p-HBCV0000JR1GE2"
    },
    {
        "id": "hb_s12_gumus",
        "name": "Hepsiburada - Tab S12 Ultra (Gümüş)",
        "site": "hepsiburada",
        "url": "https://www.hepsiburada.com/samsung-galaxy-tab-s12-ultra-12gb-ram-256gb-depolama-alani-14-6-inc-120hz-ekran-wifi7-s-pen-dahil-gumus-p-HBCV0000JR1UHB"
    },
    {
        "id": "n11_s12",
        "name": "N11 - Tab S12 Ultra",
        "site": "n11",
        "url": "https://www.n11.com/urun/samsung-galaxy-tab-s12-ultra-12-gb-256-gb-146-tablet-141574467"
    }
]

def send_telegram(text):
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(api_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")

def parse_price_str(raw_str):
    if not raw_str:
        return None
    clean = re.sub(r"[^\d,\.]", "", raw_str).strip()
    if "," in clean and "." in clean:
        clean = clean.replace(".", "").replace(",", ".")
    elif "," in clean:
        clean = clean.replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None

def fetch_price(item):
    payload = {
        'api_key': SCRAPER_API_KEY,
        'url': item["url"],
        'country_code': 'tr'
    }
    try:
        res = requests.get('https://api.scraperapi.com/', params=payload, timeout=60)
        if res.status_code != 200:
            print(f"  -> Köprü Yanıt Kodu: {res.status_code}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # 1. Schema.org JSON verisi kontrolü
        for s in soup.find_all("script", type="application/ld+json"):
