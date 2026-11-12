import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

ilceler = [
    "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler",
    "Bakırköy", "Başakşehir", "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü",
    "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy", "Esenler", "Esenyurt",
    "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane",
    "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer",
    "Silivri", "Sultanbeyli", "Sultangazi", "Şile", "Şişli", "Tuzla",
    "Ümraniye", "Üsküdar", "Zeytinburnu"
]

tr_map = str.maketrans("ğüşöçıİ", "gusocii")
eczaneler = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/json,*/*"
}

# 1. KAYNAK: Türkiye Nöbetçi Eczane Açık Sunucu (nobetcieczane.org / eczanebul)
for ilce in ilceler:
    slug = ilce.lower().translate(tr_map)
    urls = [
        f"https://www.eczanebul.net/istanbul-{slug}-nobetci-eczaneleri",
        f"https://nobetcieczane.org/istanbul/{slug}"
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                clean = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', html)
                blocks = re.split(r'<(?:h2|h3|h4|strong)[^>]*>', clean)
                found_in_page = False
                for b in blocks[1:]:
                    end = b.find('</')
                    if end == -1:
                        continue
                    ad = re.sub(r'<[^>]+>', '', b[:end]).strip()
                    if "ECZANESİ" not in ad.upper() or len(ad) > 45 or "NÖBETÇİ" in ad.upper():
                        continue
                    if any(x["ad"] == ad and x["ilce"] == ilce for x in eczaneler):
                        continue

                    snippet = re.sub(r'<[^>]+>', ' ', b[end:end+600])
                    snippet = re.sub(r'\s+', ' ', snippet).strip()
                    tel_m = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', snippet)
                    tel = tel_m.group(1).strip() if tel_m else ""
                    adres = snippet.split(tel)[0].strip() if tel else snippet[:140]
                    adres = re.sub(r'Harita|Yol Tarifi|Ara|Detay', '', adres).strip(" :-,")

                    eczaneler.append({
                        "ilce": ilce,
                        "ad": ad,
                        "adres": adres[:160],
                        "tarif": "",
                        "tel": tel,
                        "lat": "",
                        "lon": ""
                    })
                    found_in_page = True
                if found_in_page:
                    break
        except Exception:
            continue

# 2. KAYNAK (Yedek): Arama Motoru İndeksi Üzerinden Doğrudan Çekim (IP Engeli Yoktur)
if len(eczaneler) < 10:
    for ilce in ilceler:
        try:
            q = urllib.parse.quote(f"İstanbul {ilce} nöbetçi eczane eczanesi tel adres")
            ddg_url = f"https://html.duckduckgo.com/html/?q={q}"
            req = urllib.request.Request(ddg_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
                for s in snippets:
                    txt = re.sub(r'<[^>]+>', ' ', s)
                    txt = re.sub(r'\s+', ' ', txt).strip()
                    matches = re.finditer(r'([A-ZÇĞİÖŞÜ][a-zçğıöşüA-ZÇĞİÖŞÜ\s]{2,25}\s+Eczanesi)', txt)
                    for m in matches:
                        ad = m.group(1).strip()
                        if "nöbetçi" in ad.lower() or len(ad) < 8:
                            continue
                        if any(x["ad"].lower() == ad.lower() and x["ilce"] == ilce for x in eczaneler):
                            continue
                        after = txt[m.end():m.end()+180]
                        tel_m = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', after)
                        tel = tel_m.group(1).strip() if tel_m else ""
                        adres = after.split(tel)[0].strip(" :.-,") if tel else after[:110].strip(" :.-,")

                        eczaneler.append({
                            "ilce": ilce,
                            "ad": ad,
                            "adres": adres,
                            "tarif": "",
                            "tel": tel,
                            "lat": "",
                            "lon": ""
                        })
        except Exception:
            continue

tr_tz = timezone(timedelta(hours=3))
output = {
    "guncelleme": datetime.now(tr_tz).strftime("%Y-%m-%d %H:%M"),
    "kayit_sayisi": len(eczaneler),
    "liste": eczaneler
}

with open("eczaneler.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Toplam {len(eczaneler)} eczane kaydedildi.")
