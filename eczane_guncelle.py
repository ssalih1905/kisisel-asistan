import json
import re
import urllib.request
import urllib.parse
import html as html_lib
from datetime import datetime, timedelta, timezone

tr_tz = timezone(timedelta(hours=3))
now_tr = datetime.now(tr_tz)
eczaneler = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

def clean_ad(ad_raw):
    # Fazlalıkları silip sadece eczane ismini ayıklar
    ad_raw = re.sub(r'Eczanesi.*', 'Eczanesi', ad_raw, flags=re.IGNORECASE)
    parts = ad_raw.split()
    if len(parts) <= 1: return ad_raw
    
    clean_parts = []
    # Eczanesi kelimesinden geriye doğru gidip sadece Büyük harfle başlayanları alır
    for p in reversed(parts[:-1]):
        if p[0].isupper() or p[0].isdigit():
            clean_parts.insert(0, p)
        elif p.lower() in ['ve', 'yeni', 'merkez', 'büyük', 'küçük']:
            clean_parts.insert(0, p)
        else:
            break
            
    if not clean_parts:
        return parts[-2] + " Eczanesi" if len(parts) >= 2 else ad_raw
        
    return " ".join(clean_parts) + " Eczanesi"

def clean_adres(adres_raw):
    # Harita butonlarından sızan kelimeleri temizler
    adres = html_lib.unescape(adres_raw)
    adres = re.sub(r'<[^>]+>', ' ', adres)
    adres = re.sub(r'(?i)\b(al|yol|tarifi|haritada|aç|detay|telefon|tel|göster|ara|nöbetçi|eczaneler)\b', '', adres)
    adres = re.sub(r'[:\-\|]+', ' ', adres)
    adres = re.sub(r'\s+', ' ', adres).strip()
    return adres if len(adres) > 10 else "Beykoz / İstanbul"

# HTML etiketlerini boş verip sayfanın düz metninden Eczane avlayan akıllı algoritma
urls = [
    "https://www.milliyet.com.tr/nobetci-eczaneler/istanbul/beykoz/",
    "https://www.haberler.com/nobetci-eczaneler/istanbul/beykoz-nobetci-eczaneleri/",
    "https://www.hurriyet.com.tr/nobetci-eczaneler/istanbul/beykoz/",
    "https://www.sabithaber.com/nobetci-eczane/istanbul-beykoz"
]

for url in urls:
    if len(eczaneler) > 0: break  # Bir siteden listeyi aldıysa diğerlerine gitme
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
            # Düz metni çıkar
            html = re.sub(r'<script.*?</script>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
            html = re.sub(r'<style.*?</style>', ' ', html, flags=re.IGNORECASE|re.DOTALL)
            plain = re.sub(r'<[^>]+>', ' ', html)
            plain = re.sub(r'\s+', ' ', plain)
            
            # "Eczanesi" kelimesi geçen yerleri yakala
            matches = re.finditer(r'([A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]{5,35}\s+Eczanesi)', plain, re.IGNORECASE)
            
            for m in matches:
                raw_ad = m.group(1).strip()
                ad = clean_ad(raw_ad)
                
                if "nöbetçi" in ad.lower() or "bugün" in ad.lower() or len(ad) < 8: continue
                if any(e["ad"].lower() == ad.lower() for e in eczaneler): continue
                
                # Eczane isminden sonraki 200 karakter içinde telefon ara
                after = plain[m.end():m.end()+200]
                tel_m = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', after)
                
                if tel_m:
                    tel = tel_m.group(1).strip()
                    adres_raw = after.split(tel)[0]
                    adres = clean_adres(adres_raw)
                    
                    eczaneler.append({"ilce": "Beykoz", "ad": ad, "adres": adres, "tel": tel})
    except:
        pass

# Siteler yanıt vermezse bugünün tarihi ile DuckDuckGo araması yapar
if len(eczaneler) == 0:
    try:
        aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        tarih_str = f"{now_tr.day} {aylar[now_tr.month]} {now_tr.year}"
        
        q = urllib.parse.quote(f"Beykoz nöbetçi eczane {tarih_str}")
        req = urllib.request.Request(f"https://html.duckduckgo.com/html/?q={q}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
            snippets = re.findall(r'class="result__snippet"[^>]*>([\s\S]*?)</a>', html)
            
            for s in snippets:
                plain = re.sub(r'<[^>]+>', ' ', s)
                plain = re.sub(r'\s+', ' ', plain)
                
                matches = re.finditer(r'([A-ZÇĞİÖŞÜa-zçğıöşü0-9\s]{5,35}\s+Eczanesi)', plain, re.IGNORECASE)
                for m in matches:
                    raw_ad = m.group(1).strip()
                    ad = clean_ad(raw_ad)
                    
                    if "nöbetçi" in ad.lower() or "beykoz" in ad.lower() or len(ad) < 8: continue
                    if any(x["ad"].lower() == ad.lower() for x in eczaneler): continue
                    
                    after = plain[m.end():m.end()+200]
                    tel_m = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', after)
                    
                    if tel_m:
                        tel = tel_m.group(1).strip()
                        adres_raw = after.split(tel)[0]
                        adres = clean_adres(adres_raw)
                        
                        eczaneler.append({"ilce": "Beykoz", "ad": ad, "adres": adres, "tel": tel})
    except:
        pass

output = {
    "guncelleme": now_tr.strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Toplam {len(eczaneler)} eczane kaydedildi.")
