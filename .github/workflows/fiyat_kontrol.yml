import json
import os
import requests

BOT_TOKEN = "9180642674:AAF3I1uvZjswB89NXhrCCju6AgGVt2iSg6s"
CHAT_ID = "5384901785"
DATA_FILE = "fiyatlar.json"

# Doğrudan Trendyol'un iç ürün API'sini kullanıyoruz (Asla şaşmaz, bot engeline takılmaz)
PRODUCTS = [
    {
        "id": "ty_s12_gumus",
        "name": "Galaxy Tab S12 Ultra 256GB (Gümüş)",
        "content_id": "1207753922",
        "url": "https://www.trendyol.com/samsung/galaxy-tab-s12-ultra-12gb-256gb-gumus-tablet-p-1207753922"
    },
    {
        "id": "ty_s12_gri",
        "name": "Galaxy Tab S12 Ultra 256GB (Gri)",
        "content_id": "1207753924",
        "url": "https://www.trendyol.com/samsung/galaxy-tab-s12-ultra-12gb-256gb-gri-tablet-p-1207753924"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Origin": "https://www.trendyol.com",
    "Referer": "https://www.trendyol.com/"
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

def get_trendyol_price(content_id):
    api_url = f"https://public.trendyol.com/discovery-web-productgw-service/api/productDetail/{content_id}?culture=tr-TR"
    try:
        res = requests.get(api_url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            data = res.json().get("result", {})
            price_info = data.get("price", {})
            
            # İndirimli fiyat varsa onu, yoksa normal satış fiyatını alır
            discounted = price_info.get("discountedPrice", {}).get("value")
            selling = price_info.get("sellingPrice", {}).get("value")
            final_price = discounted if discounted else selling
            
            merchant_name = data.get("merchant", {}).get("name", "Trendyol Satıcısı")
            
            return final_price, merchant_name
        else:
            print(f"  -> Trendyol API Yanıt Kodu: {res.status_code}")
    except Exception as e:
        print(f"  -> İstek hatası: {e}")
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
        price, merchant = get_trendyol_price(item["content_id"])

        if not price:
            print("  -> Fiyat okunamadı.")
            continue

        old_price = history.get(item["id"])
        print(f"  -> Doğrulanan Fiyat: {price:,.2f} TL | Satıcı: {merchant} (Önceki: {old_price})")

        # İlk defa çalışıyorsa veya fiyat düştüyse haber ver
        if old_price is None:
            history[item["id"]] = price
            msg = (
                f"📌 *Gerçek Fiyat Takibi Başlatıldı*\n"
                f"*{item['name']}*\n"
                f"💰 Güncel Fiyat: `{price:,.2f} TL`\n"
                f"🏬 Satıcı: {merchant}\n"
                f"[Ürünü İncele]({item['url']})"
            )
            send_telegram(msg)
        elif price < old_price:
            diff = old_price - price
            history[item["id"]] = price
            msg = (
                f"🚨 *FİYAT DÜŞTÜ!*\n"
                f"*{item['name']}*\n"
                f"Eski Fiyat: ~{old_price:,.2f} TL~\n"
                f"Yeni Fiyat: *{price:,.2f} TL*\n"
                f"İndirim: `{diff:,.2f} TL` indirim yakalandı!\n"
                f"🏬 Satıcı: {merchant}\n"
                f"[Hemen Satın Al]({item['url']})"
            )
            send_telegram(msg)
        elif price > old_price:
            history[item["id"]] = price

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
