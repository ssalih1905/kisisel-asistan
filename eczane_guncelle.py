import json
import re
import time
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

tr_tz = timezone(timedelta(hours=3))
now_tr = datetime.now(tr_tz)
eczaneler = []

print("Görünmez Chrome hazırlanıyor...")
options = Options()
options.add_argument('--headless') # Tarayıcıyı arkaplanda görünmez açar
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

def sayfayi_tara(html_kodu):
    soup = BeautifulSoup(html_kodu, 'html.parser')
    plain = soup.get_text(separator=' ')
    plain = re.sub(r'\s+', ' ', plain)
    
    # Eczanesi kelimelerini yakala
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
            if len(adres) < 5: adres = "Beykoz / İstanbul"
            
            eczaneler.append({"ilce": "Beykoz", "ad": ad, "adres": adres, "tel": tel})

try:
    # Sistemi kur (Yaklaşık 2-3 saniye sürer)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 1. KAYNAK: BEYKOZ BELEDİYESİ
    print("Beykoz Belediyesi sistemine giriliyor (JS bekleniyor)...")
    driver.get("https://ebelediye.beykoz.bel.tr/NobetciEczane/Index/")
    time.sleep(5) # AJAX verilerinin sayfaya yüklenmesi için sihirli bekleme süresi
    sayfayi_tara(driver.page_source)
    
    # 2. KAYNAK: İSTANBUL ECZACI ODASI (Eğer belediye sistemi çökmüşse çalışır)
    if len(eczaneler) == 0:
        print("Alternatif kaynak: İEO sistemine giriliyor...")
        driver.get("https://www.istanbuleczaciodasi.org.tr/nobetci-eczane/?ilce=8")
        time.sleep(5)
        sayfayi_tara(driver.page_source)
        
except Exception as e:
    print("Görünmez Tarayıcı Hatası:", e)
finally:
    try:
        driver.quit()
    except:
        pass

output = {
    "guncelleme": now_tr.strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Başarılı! Toplam {len(eczaneler)} eczane kaydedildi.")
