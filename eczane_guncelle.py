import json
import re
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

eczaneler = []

ilceler = [
    "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler",
    "Bakırköy", "Başakşehir", "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü",
    "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy", "Esenler", "Esenyurt",
    "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane",
    "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer",
    "Silivri", "Sultanbeyli", "Sultangazi", "Şile", "Şişli", "Tuzla",
    "Ümraniye", "Üsküdar", "Zeytinburnu"
]

tr_map = str.maketrans("ğüşöçıİ", "gusocii")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        locale="tr-TR"
    )
    page = context.new_page()

    # 1. YÖNTEM: İEO sayfasında formu tetikleyip tüm listeyi çekmeyi dene
    try:
        page.goto("https://www.istanbuleczaciodasi.org.tr/nobetci-eczane/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # Sayfada arama/listeleme butonu varsa tıkla
        btn = page.query_selector("button[type='submit'], #btn-ara, .btn-search, button:has-text('Ara'), button:has-text('Listele')")
        if btn:
            btn.click()
            page.wait_for_timeout(4000)

        # Sayfadaki metin bloklarından eczane kartlarını ayıkla
        body_text = page.inner_text("body")
        if "ECZANESİ" in body_text.upper():
            blocks = page.query_selector_all("div, tr, li")
            seen = set()
            for b in blocks:
                t = b.inner_text().strip()
                if 30 < len(t) < 400 and "ECZANESİ" in t.upper() and ("0 (" in t or "0212" in t or "0216" in t):
                    lines = [x.strip() for x in t.split("\n") if x.strip()]
                    ad = next((x for x in lines if "ECZANESİ" in x.upper()), "")
                    if ad and ad not in seen:
                        seen.add(ad)
                        tel = next((x for x in lines if re.search(r'0\s*\(?21[26]\)?', x)), "")
                        ilce_bul = next((i for i in ilceler if i.lower() in t.lower()), "")
                        adres_lines = [x for x in lines if x != ad and x != tel and len(x) > 8]
                        eczaneler.append({
                            "ilce": ilce_bul,
                            "ad": ad,
                            "adres": " ".join(adres_lines[:2]),
                            "tarif": "",
                            "tel": tel,
                            "lat": "",
                            "lon": ""
                        })
    except Exception as e:
        print("İEO denemesi:", e)

    # 2. YÖNTEM (Garanti Yedek): Gerçek Chromium ile eczaneler.gen.tr ilçe sayfalarını oku
    if len(eczaneler) < 10:
        eczaneler = []
        for ilce in ilceler:
            slug = ilce.lower().translate(tr_map)
            url = f"https://www.eczaneler.gen.tr/nobetci-istanbul-{slug}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(800)
                rows = page.query_selector_all("tr")
                for row in rows:
                    isim_el = row.query_selector(".isim")
                    if not isim_el:
                        continue
                    ad = isim_el.inner_text().strip()
                    if not ad or any(x["ad"] == ad and x["ilce"] == ilce for x in eczaneler):
                        continue

                    row_text = row.inner_text()
                    tel_m = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', row_text)
                    tel = tel_m.group(1).strip() if tel_m else ""

                    lines = [l.strip() for l in row_text.split("\n") if l.strip()]
                    adres_parts = [l for l in lines if l != ad and (not tel or tel not in l) and "Harita" not in l and ilce.upper() not in l.upper()]
                    adres = " ".join(adres_parts)

                    eczaneler.append({
                        "ilce": ilce,
                        "ad": ad,
                        "adres": adres,
                        "tarif": "",
                        "tel": tel,
                        "lat": "",
                        "lon": ""
                    })
            except Exception:
                continue

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
