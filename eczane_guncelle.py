import json
import re
import time
import html as html_lib
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

tr_tz = timezone(timedelta(hours=3))
now_tr = datetime.now(tr_tz)

sorgular = [
    "Beykoz nöbetçi eczaneleri adres telefon",
    "Beykoz Merkez Kavacık nöbetçi eczane tel",
    "Paşabahçe Çubuklu Tokatköy nöbetçi eczane"
]

eczaneler = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "tr-TR,tr;q=0.9"
}

for sorgu in sorgular:
    try:
        q = urllib.parse.quote(sorgu)
        ddg_url = f"https://html.duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(ddg_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_html = resp.read().decode("utf-8", errors="ignore")
            snippets = re.findall(r'class="result__snippet"[^>]*>([\s\S]*?)</a>', raw_html)

            for s in snippets:
                txt = html_lib.unescape(re.sub(r'<[^>]+>', ' ', s))
                txt = re.sub(r'\s+', ' ', txt).strip()
                matches = re.finditer(r'([A-ZÇĞİÖŞÜ][a-zçğıöşüA-ZÇĞİÖŞÜ\s]{2,25}\s+Eczanesi)', txt)
                for m in matches:
                    ad = m.group(1).strip()
                    ad = re.sub(r'^Eczane\s+', '', ad, flags=re.IGNORECASE).strip()

                    if any(w in ad.lower() for w in ["nöbetçi", "bugün", "istanbul", "beykoz", "kavacık", "çevresinde", "açık"]):
                        continue
                    if len(ad) < 8 or any(x["ad"].lower() == ad.lower() for x in eczaneler):
                        continue

                    after = txt[m.end():m.end()+220]
                    tel_m = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', after)
                    tel = tel_m.group(1).strip() if tel_m else ""
                    
                    adres = after.split(tel)[0] if tel else after[:130]
                    adres = re.sub(r'Adres\s*:|Telefon\s*:|Tel\s*:|Yol Tarifi Al|—|\(\d+[.,]\d+\s*km\)', '', adres).strip(" :.-,)")

                    if len(adres) < 10 or "çevresinde açık eczane" in adres.lower() or "Eczanesi" in adres:
                        adres = "Beykoz / İstanbul"

                    eczaneler.append({
                        "ilce": "Beykoz",
                        "ad": ad,
                        "adres": adres,
                        "tarif": "",
                        "tel": tel,
                        "lat": "",
                        "lon": ""
                    })
        time.sleep(1.5)
    except Exception as e:
        print("Sorgu hatası:", e)

output = {
    "guncelleme": now_tr.strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Toplam {len(eczaneler)} Beykoz eczanesi kaydedildi.")
