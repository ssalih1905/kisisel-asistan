import json
import os
import requests

BOT_TOKEN = "9180642674:AAF3I1uvZjswB89NXhrCCju6AgGVt2iSg6s"
CHAT_ID = "5384901785"
DATA_FILE = "fiyatlar.json"

# Takip edilecek model ve arama sorgusu
PRODUCTS = [
    {
        "id": "tab_s12_ultra_256",
        "name": "Samsung Galaxy Tab S12 Ultra (256 GB)",
        "query": "Samsung Galaxy Tab S12 Ultra 256GB",
        "target_keywords": ["s12", "ultra", "256"]
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def send_telegram(text):
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(api_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")

def get_best_market_price(item):
    # Cimri halka açık JSON arama servisi
    search_url = f"https://api.cimri.com/v1/search?query={requests.utils.quote(item['query'])}&page=1"
    
    try:
        res = requests.get(search_url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            print(f"  -> Arama servisi yanıt kodu: {res.status_code}")
            return None, None, None

        data = res.json()
        products = data.get("data", {}).get("products", [])
        
        if not products:
            print("  -> Ürün listesi boş döndü.")
            return None, None, None

        # Doğru ürünü başlık kontrolü ile eşleştir (Kılıf, ekran koruyucu veya S9 karışmasını önler)
        for prod in products:
            title = prod.get("title", "").lower()
            if all(k in title for k in item["target_keywords"]):
                min_price = prod.get("minPrice")
                top_offer = prod.get("topOffer", {})
                merchant = top_offer.get("merchantName", "En Uygun Pazar Yeri")
                product_url = f"https://www.cimri.com/{prod.get('urlPath', '')}"
                
                if min_price:
                    return float(min_price), merchant, product_url

    except Exception as e:
        print(f"  -> İstek hatası: {e}")
        
    return None, None, None

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
        price, merchant, url = get_best_market_price(item)

        if not price:
            print("  -> Fiyat okunamadı.")
            continue

        old_price = history.get(item["id"])
        print(f"  -> Piyasa En Dip Fiyat: {price:,.2f} TL | Satıcı: {merchant} (Önceki: {old_price})")

        if old_price is None:
            history[item["id"]] = price
            msg = (
                f"📌 *Piyasa Fiyat Takibi Başlatıldı*\n"
                f"📱 *{item['name']}*\n"
                f"💰 En Düşük Fiyat: `{price:,.2f} TL`\n"
                f"🏬 En Uygun Mağaza: {merchant}\n\n"
                f"🔗 [Tüm Satıcıları ve En Ucuzu Gör]({url})"
            )
            send_telegram(msg)
        elif price < old_price:
            diff = old_price - price
            history[item["id"]] = price
            msg = (
                f"🚨 *FİYAT DÜŞTÜ!*\n"
                f"📱 *{item['name']}*\n"
                f"Eski En Düşük: ~{old_price:,.2f} TL~\n"
                f"Yeni En Düşük: *{price:,.2f} TL*\n"
                f"🔥 İndirim: `{diff:,.2f} TL`\n"
                f"🏬 Mağaza: {merchant}\n\n"
                f"🛒 [Hemen Satıcıya Git ve İncele]({url})"
            )
            send_telegram(msg)
        elif price > old_price:
            history[item["id"]] = price

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
