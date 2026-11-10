import json
import os
import re
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "9180642674:AAF3I1uvZjswB89NXhrCCju6AgGVt2iSg6s"
CHAT_ID = "5384901785"
DATA_FILE = "fiyatlar.json"

# Akakçe ve Cimri doğrudan tüm pazar yerlerinin en ucuzunu tek sayfada verir
PRODUCTS = [
    {
        "id": "akakce_s12_ultra",
        "name": "Akakçe - Galaxy Tab S12 Ultra (En Dip Fiyat)",
        "site": "akakce",
        "url": "https://www.akakce.com/tablet/en-ucuz-samsung-galaxy-tab-s12-ultra-fiyati,0.html"
    },
    {
        "id": "cimri_s12_ultra",
        "name": "Cimri - Galaxy Tab S12 Ultra (En Dip Fiyat)",
        "site": "cimri",
        "url": "https://www.cimri.com/tablet-pc/en-ucuz-samsung-galaxy-tab-s12-ultra-fiyatlari"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

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
    try:
        res = requests.get(item["url"], headers=HEADERS, timeout=20)
        if res.status_code != 200:
            print(f"  -> HTTP Durum: {res.status_code}")
            return None, None

        soup = BeautifulSoup(res.text, "html.parser")
        
        # Akakçe en ucuz fiyat ve satıcı yakalama
        if item["site"] == "akakce":
            price_el = soup.select_one("span.pt_v8, span.prc, .pt_v9, span[data-pr]")
            seller_el = soup.select_one("span.v_v8, .seller_name, span[class*='seller']")
            seller = seller_el.get_text(strip=True) if seller_el else "En Ucuz Mağaza"
            if price_el:
                return parse_price_str(price_el.get_text()), seller

        # Cimri en ucuz fiyat ve satıcı yakalama
        elif item["site"] == "cimri":
            price_el = soup.select_one("span[class*='Price'], .s1wytv2f-1, div[class*='price']")
            seller_el = soup.select_one("span[class*='Merchant'], span[class*='seller']")
            seller = seller_el.get_text(strip=True) if seller_el else "En Ucuz Mağaza"
            if price_el:
                return parse_price_str(price_el.get_text()), seller

    except Exception as e:
        print(f"  -> Hata: {e}")
    return None, None

def main():
    history = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except Exception:
                history = {}

    for item in PRODUCTS:
        print(f"Kontrol ediliyor: {item['name']}")
        price, seller = fetch_price(item)

        if not price:
            print("  -> Fiyat okunamadı.")
            continue

        old_price = history.get(item["id"])
        print(f"  -> En Ucuz Fiyat: {price:,.2f} TL | Satıcı: {seller} (Önceki: {old_price})")

        if old_price is None:
            history[item["id"]] = price
            msg = (
                f"📌 *Fiyat Takibi Başlatıldı*\n"
                f"*{item['name']}*\n"
                f"💰 En Dip Fiyat: `{price:,.2f} TL`\n"
                f"🏬 Satıcı: {seller}\n"
                f"[Fiyatları Gör ve Satıcıya Git]({item['url']})"
            )
            send_telegram(msg)
        elif price < old_price:
            diff = old_price - price
            history[item["id"]] = price
            msg = (
                f"🚨 *YENİ EN DİP FİYAT!*\n"
                f"*{item['name']}*\n"
                f"Eski Fiyat: ~{old_price:,.2f} TL~\n"
                f"Yeni En Dip Fiyat: *{price:,.2f} TL*\n"
                f"İndirim: `{diff:,.2f} TL` ucuzladı!\n"
                f"🏬 Satıcı: {seller}\n"
                f"[Hemen Satıcıya Git]({item['url']})"
            )
            send_telegram(msg)
        elif price > old_price:
            history[item["id"]] = price

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
