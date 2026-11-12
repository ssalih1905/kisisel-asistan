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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
}

def temizle(metin):
    metin = html_lib.unescape(metin)
    metin = re.sub(r'<[^>]+>', ' ', metin)
    return re.sub(r'\s+', ' ', metin).strip()

# YÖNTEM 1: Bot engeli düşük olan ulusal haber sitelerini dene
urls = [
    "https://www.hurriyet.com.tr/nobetci-eczaneler/istanbul/beykoz/",
    "https://www.haberler.com/nobetci-eczaneler/istanbul/beykoz-nobetci-eczaneleri/",
    "https://www.sabithaber.com/nobetci-eczane/istanbul-beykoz"
]

for url in urls:
    if len(eczaneler) > 0: break
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
            html = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
            
            # Eczane adını yakala
            heading_regex = r'<(?:h2|h3|h4|strong|b|a)[^>]*>\s*([A-ZÇĞİÖŞÜ][a-zçğıöşüA-ZÇĞİÖŞÜ\s]{2,30}\s+Eczanesi)\s*</(?:h2|h3|h4|strong|b|a)>'
            matches = re.finditer(heading_regex, html, re.IGNORECASE)
            
            for match in matches:
                ad = match.group(1).strip()
                if "nöbetçi" in ad.lower() or "bugün" in ad.lower() or len(ad) < 8: continue
                if any(e["ad"].lower() == ad.lower() for e in eczaneler): continue
                
                after = html[match.end():match.end()+700]
                plain = temizle(after)
                
                phone_match = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', plain)
                tel = phone_match.group(1).strip() if phone_match else ""
                
                adres = plain.split(tel)[0] if tel else plain[:120]
                adres = re.sub(r'Haritada Göster|Yol Tarifi|Ara|Detay|Nöbetçi Eczaneler', '', adres, flags=re.IGNORECASE)
                adres = re.sub(r'^[:\-\s,]+|[:\-\s,]+$', '', adres).strip()
                if len(adres) < 10: adres = "Beykoz / İstanbul"
                
                eczaneler.append({"ilce": "Beykoz", "ad": ad, "adres": adres, "tel": tel})
    except:
        pass

# YÖNTEM 2: Kesin Çözüm -> Tarih ZORUNLU Arama (Önbelleği aşmak için BUGÜNÜN TARİHİNİ arar)
if len(eczaneler) == 0:
    try:
        aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        tarih_str = f"{now_tr.day} {aylar[now_tr.month]} {now_tr.year}"
        
        # Arama sorgusuna bugünün tarihini zorunlu kılıyoruz (Örn: "12 Kasım 2026")
        q = urllib.parse.quote(f"Beykoz nöbetçi eczaneler adres {tarih_str}")
        req = urllib.request.Request(f"https://html.duckduckgo.com/html/?q={q}", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
            snippets = re.findall(r'class="result__snippet"[^>]*>([\s\S]*?)</a>', html)
            
            for s in snippets:
                plain = temizle(s)
                m = re.search(r'([A-ZÇĞİÖŞÜ][a-zçğıöşüA-ZÇĞİÖŞÜ\s]{2,25}\s+Eczanesi)', plain, re.IGNORECASE)
                if m:
                    ad = m.group(1).strip()
                    ad = re.sub(r'^Eczane\s+', '', ad, flags=re.IGNORECASE).strip()
                    if "nöbetçi" in ad.lower() or "beykoz" in ad.lower() or len(ad) < 8: continue
                    if any(x["ad"].lower() == ad.lower() for x in eczaneler): continue
                    
                    after = plain[m.end():m.end()+250]
                    tel_m = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', after)
                    tel = tel_m.group(1).strip() if tel_m else ""
                    
                    adres = after.split(tel)[0] if tel else after[:130]
                    adres = re.sub(r'Haritada Göster|Yol Tarifi|Ara|Detay|Nöbetçi Eczaneler|\(\d+[.,]\d+\s*km\)', '', adres, flags=re.IGNORECASE)
                    adres = re.sub(r'^[:\-\s,]+|[:\-\s,]+$', '', adres).strip()
                    if len(adres) < 10 or "çevresinde açık" in adres.lower(): adres = "Beykoz / İstanbul"
                    
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
