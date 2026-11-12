import json
import re
import urllib.request
import html as html_lib
from datetime import datetime, timedelta, timezone

tr_tz = timezone(timedelta(hours=3))
now_tr = datetime.now(tr_tz)
eczaneler = []

# Harika fikir! Resmi belediye sitesi Cloudflare engeline takılmaz.
target_url = "https://ebelediye.beykoz.bel.tr/NobetciEczane/Index/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

try:
    req = urllib.request.Request(target_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8')
        
        # HTML ve gereksiz kodları temizle
        html = re.sub(r'<script.*?</script>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
        html = re.sub(r'<style.*?</style>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
        
        plain = html_lib.unescape(html)
        plain = re.sub(r'<[^>]+>', ' ', plain)
        plain = re.sub(r'\s+', ' ', plain)

        # "Eczanesi" kelimelerini bul ve eşle
        matches = re.finditer(r'([A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]{5,35}\s+Eczanesi)', plain, re.IGNORECASE)
        
        for m in matches:
            ad_raw = m.group(1).strip()
            ad = re.sub(r'Eczanesi.*', 'Eczanesi', ad_raw, flags=re.IGNORECASE)
            ad = re.sub(r'^[^a-zA-ZÇĞİÖŞÜçğıöşü]+', '', ad).strip()
            
            parts = ad.split()
            if len(parts) > 1:
                clean_parts = []
                for p in reversed(parts[:-1]):
                    if p[0].isupper() or p[0].isdigit():
                        clean_parts.insert(0, p)
                    elif p.lower() in ['ve', 'yeni', 'merkez', 'büyük', 'küçük', 'ilk']:
                        clean_parts.insert(0, p)
                    else:
                        break
                ad = " ".join(clean_parts) + " Eczanesi" if clean_parts else parts[-2] + " Eczanesi"

            if "nöbetçi" in ad.lower() or "beykoz" in ad.lower() or "odası" in ad.lower() or len(ad) < 8: continue
            if any(e["ad"].lower() == ad.lower() for e in eczaneler): continue
            
            after = plain[m.end():m.end()+250]
            # 0216 veya 05XX ile başlayan telefon formatlarını bul
            tel_m = re.search(r'(0\s*216\s*[\d\s\-]{6,10}|0\s*5\d{2}\s*[\d\s\-]{6,10})', after)
            
            if tel_m:
                tel_raw = tel_m.group(1).strip()
                t = re.sub(r'[^\d]', '', tel_raw)
                tel = f"{t[0]} {t[1:4]} {t[4:7]} {t[7:9]} {t[9:11]}" if len(t) == 11 else tel_raw
                
                adres_raw = after.split(tel_raw)[0]
                adres = re.sub(r'(?i)\b(telefon|tel|adres|harita|yol|tarifi|kroki|kopyala|yazdır)\b', '', adres_raw)
                adres = re.sub(r'[:\-\|]+', ' ', adres)
                adres = re.sub(r'\s+', ' ', adres).strip()
                
                if len(adres) < 5: adres = "Beykoz / İstanbul"
                
                eczaneler.append({"ilce": "Beykoz", "ad": ad, "adres": adres, "tel": tel})
                
except Exception as e:
    print("Beykoz Bel Hata:", e)

output = {
    "guncelleme": now_tr.strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Toplam {len(eczaneler)} eczane kaydedildi.")
