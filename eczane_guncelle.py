import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup

tr_tz = timezone(timedelta(hours=3))
now_tr = datetime.now(tr_tz)
eczaneler = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

# Bot engeli OLMAYAN güvenilir ulusal kaynaklar
urls = [
    "https://www.haberturk.com/nobetci-eczane/istanbul/beykoz",
    "https://www.ntv.com.tr/nobetci-eczane/istanbul-beykoz",
    "https://www.sabithaber.com/nobetci-eczane/istanbul-beykoz"
]

for url in urls:
    if len(eczaneler) >= 2: break # Beykoz'da aynı anda en fazla 2-3 eczane nöbetçi olur
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
            
            # SİHİRLİ DOKUNUŞ: Haber sitelerinin altındaki "Diğer Eczaneler" (SEO) tuzaklarını kesip atıyoruz
            html_lower = html.lower()
            kesme_kelimeleri = ["yakındaki", "diğer eczaneler", "tüm eczaneler", "ilçesindeki diğer", "nöbetçi olmayan"]
            
            for kw in kesme_kelimeleri:
                idx = html_lower.find(kw)
                if idx != -1:
                    html = html[:idx]
                    html_lower = html_lower[:idx]

            # Kestiğimiz temiz HTML'den metni çıkarıyoruz
            soup = BeautifulSoup(html, 'html.parser')
            plain = soup.get_text(separator=' ')
            plain = re.sub(r'\s+', ' ', plain)
            
            # Sadece Eczane isimlerini avla
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
                        elif p.lower() in ['ve', 'yeni', 'merkez', 'büyük', 'küçük', 'ilk', 'nolu']:
                            clean_parts.insert(0, p)
                        else:
                            break
                    ad = " ".join(clean_parts) + " Eczanesi" if clean_parts else parts[-2] + " Eczanesi"

                if "nöbetçi" in ad.lower() or "beykoz" in ad.lower() or "odası" in ad.lower() or len(ad) < 8: continue
                if any(e["ad"].lower() == ad.lower() for e in eczaneler): continue
                
                after = plain[m.end():m.end()+250]
                # Sadece geçerli telefon formatlarını yakala
                tel_m = re.search(r'(0\s*216\s*[\d\s\-]{6,10}|0\s*5\d{2}\s*[\d\s\-]{6,10})', after)
                if tel_m:
                    tel_raw = tel_m.group(1).strip()
                    t = re.sub(r'[^\d]', '', tel_raw)
                    tel = f"{t[0]} {t[1:4]} {t[4:7]} {t[7:9]} {t[9:11]}" if len(t) == 11 else tel_raw
                    
                    adres_raw = after.split(tel_raw)[0]
                    adres = re.sub(r'(?i)\b(telefon|tel|adres|harita|yol|tarifi|kroki|kopyala|yazdır)\b', '', adres_raw)
                    adres = re.sub(r'(?i)^(istanbul|beykoz|\/|\s|-)+', '', adres)
                    adres = re.sub(r'[:\-\|]+', ' ', adres)
                    adres = re.sub(r'\s+', ' ', adres).strip()
                    
                    if len(adres) > 5:
                        eczaneler.append({"ilce": "Beykoz", "ad": ad, "adres": adres, "tel": tel})
                        
                # Maksimum 3 eczane sınırı (Yakındaki diğer ilçelerin eczanelerine kaymamak için)
                if len(eczaneler) >= 3:
                    break
    except Exception as e:
        print(f"Hata ({url}):", e)

output = {
    "guncelleme": now_tr.strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Başarılı! Toplam {len(eczaneler)} eczane kaydedildi.")
