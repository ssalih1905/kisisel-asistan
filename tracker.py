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
        return float(clean)
    except ValueError:
        return None

def fetch_price(item):
    target_url = item["url"]
    api_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={urllib.parse.quote(target_url)}"

    try:
        res = requests.get(api_url, timeout=90)
        if res.status_code != 200:
            print(f"  -> Köprü Yanıt Kodu: {res.status_code}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # 1. Hepsiburada İçin Özel: __NEXT_DATA__ JSON ayrıştırma (En Garantili Yol)
        if item["site"] == "hepsiburada":
            next_script = soup.find("script", id="__NEXT_DATA__")
            if next_script and next_script.string:
                try:
                    data = json.loads(next_script.string)
                    # Hepsiburada Next.js veri ağacında fiyatı tarar
                    raw_text = next_script.string
                    prices = re.findall(r'"price"\s*:\s*([\d\.]+)', raw_text)
                    valid_prices = [float(p) for p in prices if 40000 < float(p) < 150000]
                    if valid_prices:
                        return min(valid_prices)
                except Exception as e:
                    print(f"  -> Next Data hatası: {e}")

        # 2. Schema.org JSON-LD verisi kontrolü (N11 ve genel)
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
                price = offers.get("price") or offers.get("lowPrice")
                if price:
                    return float(str(price).replace(",", "."))
            except Exception:
                continue

        # 3. HTML CSS etiket kontrolü
        if item["site"] == "hepsiburada":
            el = soup.select_one("[data-test-id='default-price'], span[class*='price'], div[class*='PriceContainer']")
            if el:
                return parse_price_str(el.get_text())
        elif item["site"] == "n11":
            el = soup.select_one(".newPrice ins, .unf-p-summary-price, .priceDetail ins")
            if el:
                return parse_price_str(el.get_text())

    except Exception as e:
        print(f"  -> İstek hatası: {e}")
    return None

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
        price = fetch_price(item)

        if not price:
            print("  -> Fiyat okunamadı.")
            continue

        old_price = history.get(item["id"])
        print(f"  -> Bulunan Fiyat: {price:,.2f} TL (Önceki: {old_price})")

        if old_price is None:
            history[item["id"]] = price
            msg = (
                f"📌 *Fiyat Takibi Başlatıldı*\n"
                f"📱 *{item['name']}*\n"
                f"💰 Güncel Fiyat: `{price:,.2f} TL`\n"
                f"[Ürüne Git]({item['url']})"
            )
            send_telegram(msg)
        elif price < old_price:
            diff = old_price - price
            history[item["id"]] = price
            msg = (
                f"🚨 *FİYAT DÜŞTÜ!*\n"
                f"📱 *{item['name']}*\n"
                f"Eski: ~{old_price:,.2f} TL~\n"
                f"Yeni: *{price:,.2f} TL*\n"
                f"İndirim: `{diff:,.2f} TL` düştü!\n"
                f"[Hemen Satın Al]({item['url']})"
            )
            send_telegram(msg)
        elif price > old_price:
            history[item["id"]] = price

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
