import json
import urllib.request
import urllib.parse
import http.cookiejar
import re
from datetime import datetime, timedelta, timezone

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [
    ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    ("Accept-Language", "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"),
]

eczaneler = []

# 1. YÖNTEM: İstanbul Eczacı Odası Resmi Oturumlu Sorgu
try:
    base_url = "https://www.istanbuleczaciodasi.org.tr/nobetci-eczane/"
    resp1 = opener.open(base_url, timeout=25)
    page_html = resp1.read().decode("utf-8", errors="ignore")

    # Sayfa içindeki olası CSRF/token değerini yakala
    token_match = re.search(r'name=["\'](?:token|_token|csrf_token|h)["\']\s+value=["\']([^"\']+)["\']', page_html)
    post_fields = {"jx": "1", "islem": "get_nobetci_list"}
    if token_match:
        post_fields["token"] = token_match.group(1)

    req_post = urllib.request.Request(
        base_url + "index.php",
        data=urllib.parse.urlencode(post_fields).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": base_url,
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }
    )
    resp2 = opener.open(req_post, timeout=25)
    raw_json = resp2.read().decode("utf-8", errors="ignore")
    data = json.loads(raw_json)
    items = data.get("eczaneler") or data.get("list") or (data if isinstance(data, list) else [])

    for item in items:
        if isinstance(item, dict):
            eczaneler.append({
                "ilce": str(item.get("ilce") or item.get("district") or "").strip(),
                "ad": str(item.get("eczane_adi") or item.get("adi") or item.get("name") or "").strip(),
                "adres": str(item.get("adres") or item.get("address") or "").strip(),
                "tarif": str(item.get("adres_tarifi") or item.get("tarif") or "").strip(),
                "tel": str(item.get("telefon") or item.get("tel") or "").strip(),
                "lat": str(item.get("lat") or item.get("enlem") or "").strip(),
                "lon": str(item.get("lng") or item.get("lon") or item.get("boylam") or "").strip(),
            })
except Exception as e:
    print("İEO oturumlu sorgu hatası:", e)

# 2. YÖNTEM (Yedek): İlçe bazlı açık HTML taraması (GitHub Azure IP'si engellenmez)
if not eczaneler:
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

    for ilce in ilceler:
        slug = ilce.lower().translate(tr_map)
        try:
            url = f"https://www.eczaneler.gen.tr/nobetci-istanbul-{slug}"
            r = opener.open(url, timeout=15)
            h = r.read().decode("utf-8", errors="ignore")

            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.DOTALL | re.IGNORECASE)
            for row in rows:
                name_m = re.search(r'class=["\'][^"\']*isim[^"\']*["\'][^>]*>(.*?)</span>', row, re.DOTALL | re.IGNORECASE)
                if not name_m:
                    continue
                ad = re.sub(r'<[^>]+>', '', name_m.group(1)).strip()
                if not ad or any(x["ad"] == ad and x["ilce"] == ilce for x in eczaneler):
                    continue

                tel_m = re.search(r'(0\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})', row)
                tel = tel_m.group(1).strip() if tel_m else ""

                addr_m = re.search(r'class=["\'][^"\']*col-lg-6[^"\']*["\'][^>]*>(.*?)</div>', row, re.DOTALL | re.IGNORECASE)
                adres = ""
                if addr_m:
                    adres = re.sub(r'<[^>]+>', ' ', addr_m.group(1))
                    adres = re.sub(r'\s+', ' ', adres).replace(ad, "").strip()

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
