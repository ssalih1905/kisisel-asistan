import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

tr_tz = timezone(timedelta(hours=3))
now_tr = datetime.now(tr_tz)
eczaneler = []

target_url = "https://www.eczaneler.gen.tr/nobetci-istanbul-beykoz"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

html = ""

# YÖNTEM 1: Doğrudan erişim
try:
    print("Doğrudan erişim deneniyor...")
    req = urllib.request.Request(target_url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8')
except Exception as e1:
    print(f"Doğrudan erişim engellendi ({e1}). Proxy 1 deneniyor...")
    # YÖNTEM 2: Ücretsiz Proxy (CodeTabs) üzerinden erişim
    try:
        proxy1 = f"https://api.codetabs.com/v1/proxy?quest={target_url}"
        req = urllib.request.Request(proxy1, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
    except Exception as e2:
        print(f"Proxy 1 engellendi ({e2}). Proxy 2 deneniyor...")
        # YÖNTEM 3: Ücretsiz Proxy (AllOrigins) üzerinden erişim
        try:
            proxy2 = f"https://api.allorigins.win/get?url={urllib.parse.quote(target_url)}"
            req = urllib.request.Request(proxy2, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                html = data.get("contents", "")
        except Exception as e3:
            print(f"Tüm erişim yöntemleri başarısız: {e3}")

if html and "text-title" in html:
    # eczaneler.gen.tr sitesinin özel HTML yapısını ayıklıyoruz
    blocks = html.split('class="text-title"')
    for block in blocks[1:]:
        try:
            # 1. Eczane Adı (Link etiketlerini sökerek alır)
            name_raw = block.split('</span>')[0]
            ad = re.sub(r'<[^>]+>', ' ', name_raw).strip()
            if not ad: continue
            if "eczane" not in ad.lower():
                ad += " Eczanesi"
                
            # 2. Adres (Adres kutusunu bulup içindeki HTML'leri temizler)
            adres_match = re.search(r'class="text-content"[^>]*>([\s\S]*?)</div>', block)
            if adres_match:
                adres_raw = adres_match.group(1)
                adres = re.sub(r'<[^>]+>', '
