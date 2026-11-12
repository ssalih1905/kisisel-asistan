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
    # YÖNTEM 2: Ücretsiz Proxy (CodeTabs)
    try:
        proxy1 = f"https://api.codetabs.com/v1/proxy?quest={target_url}"
        req = urllib.request.Request(proxy1, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8')
    except Exception as e2:
        print(f"Proxy 1 engellendi ({e2}). Proxy 2 deneniyor...")
        # YÖNTEM 3: Ücretsiz Proxy (AllOrigins)
        try:
            proxy2 = f"https://api.allorigins.win/get?url={urllib.parse.quote(target_url)}"
            req = urllib.request.Request(proxy2, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                html = data.get("contents", "")
        except Exception as e3:
            print(f"Tüm erişim yöntemleri başarısız: {e3}")

if html and "text-title" in html:
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

output = {
    "guncelleme": now_tr.strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Toplam {len(eczaneler)} eczane kaydedildi.")
