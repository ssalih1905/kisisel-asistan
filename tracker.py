import json
import os
import re
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = "9180642674:AAF3I1uvZjswB89NXhrCCju6AgGVt2iSg6s"
CHAT_ID = "5384901785"
DATA_FILE = "fiyatlar.json"

PRODUCTS = [
    {
        "id": "mm_s12_gri",
        "name": "MediaMarkt - Tab S12 Ultra (Gri)",
        "site": "mediamarkt",
        "url": "https://www.mediamarkt.com.tr/tr/product/_samsung-galaxy-tab-s12-ultra-12256gb-tam-dokunmatik-tablet-gri-1257344.html"
    },
    {
        "id": "mm_s12_gumus",
        "name": "MediaMarkt - Tab S12 Ultra (Gümüş)",
        "site": "mediamarkt",
        "url": "https://www.mediamarkt.com.tr/tr/product/_samsung-galaxy-tab-s12-ultra-12256gb-tam-dokunmatik-tablet-gumus-1257345.html"
    },
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
        "id": "ty_s12_gumus",
        "name": "Trendyol - Tab S12 Ultra (Gümüş)",
        "site": "trendyol",
        "url": "https://www.trendyol.com/samsung/galaxy-tab-s12-ultra-12gb-256gb-gumus-tablet-p-1207753922?boutiqueId=689770&merchantId=968"
    },
    {
        "id": "ty_s12_gri",
        "name": "Trendyol - Tab S12 Ultra (Gri)",
        "site": "trendyol",
        "url": "https://www.trendyol.com/samsung/galaxy-tab-s12-ultra-12gb-256gb-gri-tablet-p-1207753924?boutiqueId=689770&merchantId=968"
    },
    {
        "id": "n11_s12_gumus",
        "name": "N11 - Tab S12 Ultra (Gümüş)",
        "site": "n11",
        "url": "https://www.n11.com/urun/samsung-galaxy-tab-s12-ultra-12-gb-256-gb-146-tablet-141574467?magaza=scenter&renk=gumus"
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

def fetch_price(page, item):
    page.goto(item["url"], wait_until="domcontentloaded", timeout=35000)
    page.wait_for_timeout(3000)
    site = item["site"]
    price_val = None

    if site == "hepsiburada":
        el = page.query_selector("[data-test-id='default-price'], [data-test-id='price-current-price'], span[class*='price']")
        if el:
            price_val = parse_price_str(el.inner_text())
    elif site == "trendyol":
        el = page.query_selector(".prc-dsc, span.discounted, .product-price-container")
        if el:
            price_val = parse_price_str(el.inner_text())
    elif site == "mediamarkt":
        el = page.query_selector("span[data-test='branded-price-whole'], [class*='Pricestyled']")
        if el:
            price_val = parse_price_str(el.inner_text())
    elif site == "n11":
        el = page.query_selector(".newPrice ins, .unf-p-summary-price, .priceDetail ins")
        if el:
            price_val = parse_price_str(el.inner_text())

    return price_val

def main():
    history = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except Exception:
                history = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for item in PRODUCTS:
            try:
                print(f"Kontrol ediliyor: {item['name']}")
                price = fetch_price(page, item)
                
                if price is None:
                    print("  -> Fiyat okunamadı.")
                    continue

                old_price = history.get(item["id"])
                print(f"  -> Bulunan: {price} TL (Önceki: {old_price})")

                if old_price is None:
                    history[item["id"]] = price
                    msg = f"📌 *Fiyat Takibi Başlatıldı*\n*{item['name']}*\nBaşlangıç Fiyatı: `{price:,.2f} TL`\n[Ürüne Git]({item['url']})"
                    send_telegram(msg)
                elif price < old_price:
                    diff = old_price - price
                    history[item["id"]] = price
                    msg = (
                        f"🚨 *FİYAT DÜŞTÜ!*\n"
                        f"*{item['name']}*\n"
                        f"Eski: ~{old_price:,.2f} TL~\n"
                        f"Yeni: *{price:,.2f} TL*\n"
                        f"İndirim: `{diff:,.2f} TL`\n"
                        f"[Ürüne Git]({item['url']})"
                    )
                    send_telegram(msg)
                elif price > old_price:
                    history[item["id"]] = price

            except Exception as e:
                print(f"Hata ({item['name']}): {e}")

        browser.close()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
