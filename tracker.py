import json
import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "9180642674:AAF3I1uvZjswB89NXhrCCju6AgGVt2iSg6s"
CHAT_ID = "5384901785"
DATA_FILE = "fiyatlar.json"

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
        val = float(clean)
        return val if 30000 < val < 200000 else None
    except ValueError:
        return None

def fetch_price(item):
    target_url = item["url"]
    
    # Hepsiburada JS render istediği için render=true ekliyoruz, N11 için düz istek yetiyor
    if item["site"] == "hepsiburada":
        api_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={urllib.parse.quote(target_url)}&render=true"
    else:
        api_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={urllib.parse.quote(target_url)}"

    try:
        res = requests.get(api_url, timeout=90)
        if res.status_code != 200:
            print(f"  -> Köprü Yanıt Kodu: {res.status_code}")
            return None

        html_text = res.text
        soup = BeautifulSoup(html_text, "html.parser")

        # 1. Hepsiburada DOM ve Veri Alanı Taraması
        if item["site"] == "hepsiburada":
            # JS ile render edilmiş DOM elemanları
            selectors = [
                "[data-test-id='default-price']",
                "[data-test-id='price-current-price']",
                "span[class*='price']",
                "div[class*='PriceContainer'] span",
                "span.price-item"
            ]
            for sel in selectors:
                for el in soup.select(sel):
                    val = parse_price_str(el.get_text())
                    if val:
                        return val

            # Sayfa içi JSON state verilerini arama (Next.js state objesi)
            price_matches = re.findall(r'"(?:price|sellingPrice|currentPrice|customerPrice)"\s*:\s*([\d\.]+)', html_text)
            valid = [float(p) for p in price_matches if 40000 < float(p) < 150000]
            if valid:
                return min(valid)

        # 2. N11 ve Genel Schema.org JSON-LD Taraması
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            if not s.string:
                continue
            try:
                data = json.loads(s.string)
                if isinstance(data, list):
                    data = data[0]
                offers = data.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0]
                raw_p = offers.get("price") or offers.get("lowPrice")
                if raw_p:
                    val = float(str(raw_p).replace(",", "."))
                    if 30000 < val < 200000:
                        return val
            except Exception:
                continue

        # 3. N11 HTML CSS Seçicileri
        if item["site"] == "n11":
            el = soup.select_
