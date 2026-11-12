import json
import re
from datetime import datetime, timedelta, timezone
import cloudscraper

tr_tz = timezone(timedelta(hours=3))
now_tr = datetime.now(tr_tz)
eczaneler = []

target_url = "https://www.eczaneler.gen.tr/nobetci-istanbul-beykoz"

# Cloudscraper ile Cloudflare korumasını gerçek bir tarayıcı gibi taklit ederek aşıyoruz
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

try:
    print("Cloudscraper ile eczaneler.gen.tr sitesine bağlanılıyor...")
    resp = scraper.get(target_url, timeout=20)
    html = resp.text

    if "text-title" in html:
        blocks = html.split('class="text-title"')
        for block in blocks[1:]:
            try:
                name_raw = block.split('</span>')[0]
                ad = re.sub(r'<[^>]+>', ' ', name_raw).strip()
                if not ad: continue
                if "eczane" not in ad.lower():
                    ad += " Eczanesi"
                    
                adres_match = re.search(r'class="text-content"[^>]*>([\s\S]*?)</div>', block)
                if adres_match:
                    adres_raw = adres_match.group(1)
                    adres = re.sub(r'<[^>]+>', ' ', adres_raw)
                    adres = re.sub(r'\s+', ' ', adres).strip()
                else:
                    adres = "Beykoz / İstanbul"
                    
                tel_match = re.search(r'href="tel:([^"]+)"', block)
                if tel_match:
                    tel_raw = tel_match.group(1).replace(" ", "").replace("+9", "")
                    if len(tel_raw) == 11 and tel_raw.startswith("0"):
                        tel = f"{tel_raw[0]} {tel_raw[1:4]} {tel_raw[4:7]} {tel_raw[7:9]} {tel_raw[9:11]}"
                    else:
                        tel = tel_raw
                else:
                    tel = ""
                    
                if not any(e["ad"] == ad for e in eczaneler):
                    eczaneler.append({"ilce": "Beykoz", "ad": ad, "adres": adres, "tel": tel})
            except Exception as e:
                continue
except Exception as e:
    print("Bağlantı Hatası:", e)

output = {
    "guncelleme": now_tr.strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Toplam {len(eczaneler)} eczane kaydedildi.")
