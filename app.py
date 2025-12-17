from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# DOĞRU HEDEF: RealGM EuroLeague Fikstür Sayfası
TARGET_URL = "https://basketball.realgm.com/international/league/1/Euroleague/schedules"

@app.route('/', methods=['GET'])
def home():
    return "<h1>EuroLeague API Online</h1><p>Git: <a href='/euroleague'>/euroleague</a></p>"

@app.route('/euroleague', methods=['GET'])
def get_schedule():
    try:
        # RealGM botları engellemesin diye gerçek tarayıcı taklidi yapıyoruz
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # Siteye bağlan
        response = requests.get(TARGET_URL, headers=headers)
        
        if response.status_code != 200:
            return jsonify([{"error": f"Site Acilmadi. Hata Kodu: {response.status_code}"}])

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # RealGM'de fikstür tablosunu bul
        # Genelde sayfanın ilk tablosudur
        table = soup.find('table') 
        
        if not table:
             # Bazen mobilde tablo farklıdır, alternatif arama
            return jsonify([{"error": "Tablo Bulunamadı. HTML Yapisi Farkli Olabilir."}])

        rows = table.find('tbody').find_all('tr')
        matches = []
        match_id = 1
        current_date = "Tarih Yok"

        for row in rows:
            cols = row.find_all('td')
            # Satırda en az 3 veri olmalı (Tarih/Ev/Dep)
            if len(cols) < 3: 
                continue

            # Tarih sütunu (Genelde ilk sütun)
            date_text = cols[0].get_text(strip=True)
            if date_text:
                current_date = date_text
            
            # Takımlar ve Skorlar
            # RealGM Yapısı: [Tarih, Ev Sahibi, Skor/Saat, Deplasman, ...]
            home_team = cols[1].get_text(strip=True)
            result_col = cols[2].get_text(strip=True)
            away_team = cols[3].get_text(strip=True)
            
            home_score = "-"
            away_score = "-"
            status = result_col
            is_live = False

            # Skor Kontrolü (Örn: "88-74" veya "W 90-80")
            if "-" in result_col and ":" not in result_col:
                parts = result_col.replace("W ","").replace("L ","").split("-")
                if len(parts) >= 2:
                    home_score = parts[0].strip()
                    away_score = parts[1].strip()
                    status = "FINAL"
            else:
                # Oynanmamış maç (Örn: "20:45")
                status = result_col

            # Logo Oluşturucu
            h_logo = f"https://ui-avatars.com/api/?name={home_team}&background=random&color=fff&size=128"
            a_logo = f"https://ui-avatars.com/api/?name={away_team}&background=random&color=fff&size=128"

            matches.append({
                "id": match_id,
                "date": current_date,
                "homeTeam": home_team,
                "awayTeam": away_team,
                "homeScore": home_score,
                "awayScore": away_score,
                "status": status,
                "isLive": is_live,
                "homeLogo": h_logo,
                "awayLogo": a_logo
            })
            match_id += 1

        # En son oynanan maçları görmek için listeyi ters çevirip ilk 50'yi al
        # RealGM geleceği de gösterir, ters çevirince en son sonuçlar üste gelir.
        return jsonify(matches[::-1][:50])

    except Exception as e:
        return jsonify([{"error": str(e)}])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=5000)

