import json
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

eczaneler = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        locale="tr-TR"
    )
    page = context.new_page()

    # İEO arka planda dönen JSON yanıtını doğrudan yakala
    def handle_response(response):
        if "nobetci-eczane" in response.url and response.status == 200:
            try:
                if "json" in response.headers.get("content-type", ""):
                    data = response.json()
                    items = data.get("eczaneler") or data.get("list") or (data if isinstance(data, list) else [])
                    for item in items:
                        if isinstance(item, dict) and (item.get("eczane_adi") or item.get("adi")):
                            eczaneler.append({
                                "ilce": str(item.get("ilce") or "").strip(),
                                "ad": str(item.get("eczane_adi") or item.get("adi") or "").strip(),
                                "adres": str(item.get("adres") or "").strip(),
                                "tarif": str(item.get("adres_tarifi") or item.get("tarif") or "").strip(),
                                "tel": str(item.get("telefon") or item.get("tel") or "").strip(),
                                "lat": str(item.get("lat") or item.get("enlem") or "").strip(),
                                "lon": str(item.get("lng") or item.get("lon") or item.get("boylam") or "").strip(),
                            })
            except Exception:
                pass

    page.on("response", handle_response)

    try:
        page.goto("https://www.istanbuleczaciodasi.org.tr/nobetci-eczane/", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(4000)
    except Exception as e:
        print("İEO sayfa hatası:", e)

    # Eğer XHR yakalanmadıysa sayfadaki görünür DOM kartlarını oku
    if not eczaneler:
        cards = page.query_selector_all(".eczane-karti, .nobetci-eczane, table tr")
        for card in cards:
            txt = card.inner_text().strip()
            if "ECZANESİ" in txt.upper() and len(txt) > 20:
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                eczaneler.append({
                    "ilce": lines[1] if len(lines) > 1 else "",
                    "ad": lines[0],
                    "adres": " ".join(lines[2:-1]) if len(lines) > 3 else (lines[2] if len(lines) > 2 else ""),
                    "tarif": "",
                    "tel": lines[-1] if any(c.isdigit() for c in lines[-1]) else "",
                    "lat": "",
                    "lon": ""
                })

    browser.close()

tr_tz = timezone(timedelta(hours=3))
output = {
    "guncelleme": datetime.now(tr_tz).strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Toplam {len(eczaneler)} eczane kaydedildi.")
