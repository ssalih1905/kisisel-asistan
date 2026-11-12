import json
import urllib.request
import re
from datetime import datetime, timedelta, timezone

URL = "https://www.istanbuleczaciodasi.org.tr/nobetci-eczane/"

req = urllib.request.Request(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9"
    }
)

try:
    with urllib.request.urlopen(req, timeout=25) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
except Exception as e:
    print("Bağlantı hatası:", e)
    html = ""

eczaneler = []

json_match = re.search(r'(?:eczaneler|eczaneListesi|locations)\s*=\s*(\[\{.*?\}\]);', html, re.DOTALL)
if json_match:
    try:
        raw_list = json.loads(json_match.group(1))
        for item in raw_list:
            eczaneler.append({
                "ilce": item.get("ilce", ""),
                "ad": item.get("eczane_adi") or item.get("adi") or item.get("name", ""),
                "adres": item.get("adres") or item.get("address", ""),
                "tarif": item.get("adres_tarifi") or item.get("tarif", ""),
                "tel": item.get("telefon") or item.get("tel", ""),
                "lat": item.get("lat") or item.get("enlem", ""),
                "lon": item.get("lng") or item.get("lon") or item.get("boylam", "")
            })
    except Exception as e:
        print("JSON ayrıştırma hatası:", e)

tr_tz = timezone(timedelta(hours=3))
output = {
    "guncelleme": datetime.now(tr_tz).strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Toplam {len(eczaneler)} eczane kaydedildi.")
