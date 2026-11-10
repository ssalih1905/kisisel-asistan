import json
import os
import re
import requests
from bs4 import BeautifulSoup

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
        "url": "https://www.trendyol.com/samsung/galaxy-tab-s12-ultra-12gb-256gb-gumus-tablet-p-1207753922"
    },
    {
        "id": "ty_s12_gri",
        "name": "Trendyol - Tab S12 Ultra (Gri)",
        "site": "trendyol",
        "url": "https://www.trendyol.com/samsung/galaxy-tab-s12-ultra-12gb-256gb-gri-tablet-p-1207753924"
    },
    {
        "id": "n11_s12_genel",
        "name": "N11 - Tab S12 Ultra (En Uygun Satıcı)",
        "site": "n11",
        "url": "https://www.n11.com/urun/samsung-galaxy-tab-s12-ultra-12-gb-256-gb-146-tablet-141574467"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
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

def parse_price(html_text):
    """HTML içindeki Schema.org JSON-LD veya gizli metadata fiyat etiketlerini bulur."""
    # 1. Regex ile "price": 64999 veya "price":"64999.00" arayışı
    matches = re.findall(r'"price"\s*:\s*"?([\d\.,]+)"?', html_text)
    valid_prices = []
    for m in matches:
        clean = m.replace(".", "").replace(",", ".")
        try:
            val = float(clean)
            if 10000 < val < 200000:  # Tablet fiyat aralığına uygun olanları filtreler
                valid_prices.append(val)
        except ValueError:
            continue
    if valid_prices:
        return min(valid_prices)

    # 2. JSON-LD bloklarını ayrıştırma
    soup = BeautifulSoup(html_text, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]
            offers = data.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0]
            raw_p = offers.get("price") or offers.get("lowPrice")
            if raw_p:
                return float(str(raw_p).replace(",", "."))
        except Exception:
            continue

    return None

def fetch_price(item):
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        res = session.get(item["url"], timeout=20)
        if res.status_code == 200:
            return parse_price(res.text)
        else:
            print(f"  -> HTTP Durum Kodu: {res.status_code}")
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

    summary_list = []

    for item in PRODUCTS:
        print(f"Kontrol ediliyor: {item['name']}")
        price = fetch_price(item)

        if price is None:
            print("  -> Fiyat okunamadı.")
            continue

        old_price = history.get(item["id"])
        print(f"  -> Bulunan: {price:,.2f} TL (Önceki: {old_price})")
        summary_list.append(f"• *{item['name']}*: `{price:,.2f} TL`")

        if old_price is None:
            history[item["id"]] = price
            msg = f"📌 *Fiyat Takibi Başlatıldı*\n*{item['name']}*\nİlk Fiyat: `{price:,.2f} TL`\n[Ürüne Git]({item['url']})"
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

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
