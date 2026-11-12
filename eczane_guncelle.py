import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone

tr_tz = timezone(timedelta(hours=3))
now_tr = datetime.now(tr_tz)
eczaneler = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml"
}

# Kaynak 1: eczaneler.gen.tr (Doğrudan Gerçek Zamanlı Veri)
try:
    req = urllib.request.Request("https://www.eczaneler.gen.tr/nobetci-istanbul-beykoz", headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8')
        parts = html.split('class="text-title"')
        for p in parts[1:]:
            ad_m = re.search(r'>([^<]+)</span>', p)
            if not ad_m: continue
            ad = ad_m.group(1).strip()
            if "eczane" not in ad.lower(): ad += " Eczanesi"
            
            adres_m = re.search(r'class="text-content"[^>]*>([\s\S]*?)</div>', p)
            adres = re.sub(r'<[^>]+>', ' ', adres_m.group(1)).strip() if adres_m else "Beykoz / İstanbul"
            adres = re.sub(r'\s+', ' ', adres)
            
            tel_m = re.search(r'href="tel:([^"]+)"', p)
            tel = tel_m.group(1).replace(" ", "") if tel_m else ""
            if len(tel) == 11 and tel.startswith("0"):
                tel = f"{tel[0]} {tel[1:4]} {tel[4:7]} {tel[7:9]} {tel[9:11]}"
            
            if not any(e["ad"] == ad for e in eczaneler):
                eczaneler.append({"ilce": "Beykoz", "ad": ad, "adres": adres, "tel": tel})
except Exception as e:
    print("Kaynak 1 Hata:", e)

# Kaynak 2: haberler.com (Alternatif Yedek)
if len(eczaneler) == 0:
    try:
        req = urllib.request.Request("https://www.haberler.com/nobetci-eczaneler/istanbul/beykoz-nobetci-eczaneleri/", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
            matches = re.finditer(r'<(?:h2|h3|h4|strong)[^>]*>([\s\S]*?)</(?:h2|h3|h4|strong)>', html)
            for match in matches:
                raw_title = re.sub(r'<[^>]+>', ' ', match.group(1)).strip()
                if "eczanesi" not in raw_title.lower() or "nöbetçi" in raw_title.lower() or len(raw_title) < 5: continue
                if any(e["ad"].lower() == raw_title.lower() for e in eczaneler): continue
                
                after = html[match.end():match.end()+600]
                plain = re.sub(r'<[^>]+>', ' ', after)
                plain = re.sub(r'\s+', ' ', plain).strip()
                
                phone_match = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', plain)
                tel = phone_match.group(1).strip() if phone_match else ""
                
                adres = plain.split(tel)[0] if tel else plain[:120]
                adres = re.sub(r'Haritada Göster|Yol Tarifi|Ara|Detay|Nöbetçi Eczaneler', '', adres, flags=re.IGNORECASE)
                adres = re.sub(r'^[:\-\s,]+|[:\-\s,]+$', '', adres).strip()
                if len(adres) < 10: adres = "Beykoz / İstanbul"
                
                eczaneler.append({"ilce": "Beykoz", "ad": raw_title, "adres": adres, "tel": tel})
    except Exception as e:
        print("Kaynak 2 Hata:", e)

output = {
    "guncelleme": now_tr.strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"{len(eczaneler)} eczane kaydedildi.")
