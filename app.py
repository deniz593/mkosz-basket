from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os
import datetime

app = Flask(__name__)

# HEDEF: Basketball Reference 2024-2025 EuroLeague Sezonu
TARGET_URL = "https://www.basketball-reference.com/leagues/Euroleague_2025_games.html"

@app.route('/', methods=['GET'])
def home():
    return "EuroLeague API (Real Data) Online."

@app.route('/euroleague', methods=['GET'])
def get_real_data():
    matches = []
    try:
        # 1. Siteye, gerçek bir tarayıcı gibi istek atıyoruz
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(TARGET_URL, headers=headers)
        
        if response.status_code != 200:
            return jsonify([{"error": "Siteye ulasilamadi"}])

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. Fikstür Tablosunu Bul ('schedule' id'li tablo)
        table = soup.find('table', {'id': 'schedule'})
        if not table:
            return jsonify([])

        rows = table.find('tbody').find_all('tr')
        
        # Maçları işle
        match_id = 1
        today = datetime.date.today()
        
        # Sonuçları tersten tarayıp en güncelleri alabiliriz veya hepsini alabiliriz
        # Biz son 5 oynanan ve gelecek 5 maçı alalım ki liste çok şişmesin
        processed_matches = []

        for row in rows:
            # Başlık satırlarını atla (thead class içerenler)
            if 'thead' in row.get('class', []):
                continue
            
            cols = row.find_all('td')
            th = row.find('th') # Tarih genelde th içindedir bu sitede
            
            if cols and th:
                date_text = th.get_text(strip=True) # Örn: Thu, Oct 3, 2024
                
                # Sütun İndeksleri (Basketball-Ref yapısına göre):
                # 0: Visitor Team, 1: Visitor Pts, 2: Home Team, 3: Home Pts
                visitor_team = cols[0].get_text(strip=True)
                visitor_pts = cols[1].get_text(strip=True)
                home_team = cols[2].get_text(strip=True)
                home_pts = cols[3].get_text(strip=True)
                
                # Logo URL'lerini takım ismine göre dinamik oluşturuyoruz (Wikimedia)
                # Basit bir eşleştirme mantığı
                
                status = "MS" # Varsayılan: Maç Sonu
                score_home = home_pts
                score_away = visitor_pts
                is_live = False

                # Eğer puanlar boşsa maç oynanmamıştır
                if not home_pts or not visitor_pts:
                    status = date_text # Tarihi durum olarak göster
                    score_home = "-"
                    score_away = "-"
                
                processed_matches.append({
                    "id": match_id,
                    "round": "EuroLeague 24/25",
                    "date": date_text,
                    "homeTeam": home_team,
                    "awayTeam": visitor_team,
                    "homeScore": score_home,
                    "awayScore": score_away,
                    "status": status,
                    "isLive": is_live,
                    # Logolar için Wikipedia API veya sabit CDN kullanılabilir, şimdilik placeholder
                    "homeLogo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/03/EuroLeague_logo.svg/1200px-EuroLeague_logo.svg.png", 
                    "awayLogo": "https://upload.wikimedia.org/wikipedia/en/thumb/0/03/EuroLeague_logo.svg/1200px-EuroLeague_logo.svg.png"
                })
                match_id += 1
        
        # Veriyi JSON olarak dön (Ters çevir ki en son maçlar üstte olsun)
        return jsonify(processed_matches[::-1])

    except Exception as e:
        print(f"Hata: {e}")
        return jsonify([])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
