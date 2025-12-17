from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os
import datetime

app = Flask(__name__)

# GÜNCELLENDİ: 2025-2026 Sezonu Linki (Basketball Ref. sezonları bitiş yılıyla adlandırır)
TARGET_URL = "https://www.basketball-reference.com/leagues/Euroleague_2026_games.html"

@app.route('/euroleague', methods=['GET'])
def get_season_data():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(TARGET_URL, headers=headers)
        
        # Eğer 2026 sayfası henüz yoksa (bazen geç açılır), 2025'e düşmemesi için kontrol
        if response.status_code != 200:
            return jsonify([{"error": "2026 Verisi Henüz Yayınlanmamış veya Siteye Erişilemiyor"}])

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'schedule'})
        
        if not table:
            return jsonify([])

        rows = table.find('tbody').find_all('tr')
        matches = []
        match_id = 1
        
        # Bugünün tarihi (Simülasyon ortamında gerçek tarih neyse onu alır)
        today = datetime.date.today()

        for row in rows:
            if 'thead' in row.get('class', []): continue
            
            cols = row.find_all('td')
            th = row.find('th') # Tarih sütunu
            
            if cols and th:
                date_str = th.get_text(strip=True) # Örn: Thu, Dec 18, 2025
                
                # Verileri al
                visitor = cols[0].get_text(strip=True)
                visitor_pts = cols[1].get_text(strip=True)
                home = cols[2].get_text(strip=True)
                home_pts = cols[3].get_text(strip=True)
                
                # Durum Belirleme
                status = "MS"
                is_live = False
                
                # Puanlar boşsa maç gelecektedir veya şu an oynanıyordur
                if not home_pts:
                    status = "20:45" # Varsayılan saat (Site saati vermiyorsa)
                    home_pts = "-"
                    visitor_pts = "-"
                    
                    # Eğer tarih bugüne eşitse "CANLI" muamelesi yapabiliriz
                    # (Basit bir mantıkla)
                    if str(today.day) in date_str and str(today.month) in date_str:
                         status = "LIVE"
                         is_live = True

                matches.append({
                    "id": match_id,
                    "date": date_str,
                    "homeTeam": home,
                    "awayTeam": visitor,
                    "homeScore": home_pts,
                    "awayScore": visitor_pts,
                    "status": status,
                    "isLive": is_live,
                    # Logolar için Wikipedia kullanıyoruz (Takım ismine göre)
                    "homeLogo": f"https://ui-avatars.com/api/?name={home}&background=random&color=fff", 
                    "awayLogo": f"https://ui-avatars.com/api/?name={visitor}&background=random&color=fff"
                })
                match_id += 1
        
        # Listeyi ters çevir (En güncel maçlar üstte olsun)
        return jsonify(matches[::-1])

    except Exception as e:
        return jsonify([{"error": str(e)}])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
