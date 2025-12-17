from flask import Flask, jsonify
import pandas as pd
import io
import requests
import os

app = Flask(__name__)

# DOĞRU KAYNAK: IvoVillanueva'nın GitHub'ındaki RAW CSV dosyası
CSV_URL = "https://raw.githubusercontent.com/IvoVillanueva/BOXSCORES-EUROLEAGE-2025_26/main/data/euroleague_boxscore_2025_26.csv"

@app.route('/', methods=['GET'])
def home():
    return "<h1>EuroLeague Resmi Veri Sunucusu</h1><p>Veriler icin: <a href='/euroleague'>/euroleague</a></p>"

@app.route('/euroleague', methods=['GET'])
def get_csv_data():
    try:
        # 1. CSV'yi GitHub'dan çek
        response = requests.get(CSV_URL)
        if response.status_code != 200:
            return jsonify([{"error": "Veri Kaynagina Ulasilamadi"}]), 500

        # 2. Pandas ile oku (CSV işlemek için en iyisi)
        # CSV içeriğini bir bellek dosyası gibi okuyoruz
        df = pd.read_csv(io.StringIO(response.text))
        
        # 3. Veriyi Sadeleştir (Mobil uygulama için sadece maç sonuçlarını alalım)
        # Bu CSV oyuncu bazlıdır (Boxscore). Maç skorunu bulmak için gruplama yapmalıyız.
        
        # Gerekli sütunlar (Tahmini sütun isimleri - repoya göre değişebilir ama genelde standarttır)
        # Depo açıklamasında 'team_name', 'opp_team_name', 'pts', 'id_match', 'date', 'ronda' olduğu yazıyor.
        
        # Her maç ID'si için takımların toplam puanlarını hesapla
        match_scores = df.groupby(['id_match', 'team_name', 'opp_team_name', 'date', 'ronda'])['pts'].sum().reset_index()
        
        # Şimdi bunu "Ev Sahibi - Deplasman" formatına çevirelim
        # Her maç için 2 satır vardır (A vs B ve B vs A). Tekilleştirmemiz lazım.
        
        unique_matches = []
        processed_ids = set()

        for index, row in match_scores.iterrows():
            match_id = row['id_match']
            
            if match_id in processed_ids:
                continue
            
            # Bu maçın diğer takımının skorunu bul
            # Aynı maç ID'sine sahip diğer satırı buluyoruz
            opponent_row = match_scores[
                (match_scores['id_match'] == match_id) & 
                (match_scores['team_name'] != row['team_name'])
            ]
            
            if not opponent_row.empty:
                opp_score = opponent_row.iloc[0]['pts']
                
                # Takım A (row) ve Takım B (opponent_row)
                home_team = row['team_name']
                home_score = int(row['pts'])
                
                away_team = row['opp_team_name']
                away_score = int(opp_score)
                
                # Logo Oluşturucu
                h_logo = f"https://ui-avatars.com/api/?name={home_team}&background=random&color=fff&size=128&bold=true"
                a_logo = f"https://ui-avatars.com/api/?name={away_team}&background=random&color=fff&size=128&bold=true"

                unique_matches.append({
                    "id": int(match_id),
                    "round": str(row['ronda']), # Örn: "Round 1"
                    "date": str(row['date']),
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "homeScore": str(home_score),
                    "awayScore": str(away_score),
                    "status": "FINAL", # CSV'de sadece bitmiş maçlar olur
                    "isLive": False,
                    "homeLogo": h_logo,
                    "awayLogo": a_logo
                })
                
                processed_ids.add(match_id)

        # En son oynanan maçları (Tarihe veya ID'ye göre) sırala
        # Pandas DataFrame olmadığı için listeyi id'ye göre ters çevirelim
        unique_matches.sort(key=lambda x: x['id'], reverse=True)

        return jsonify(unique_matches)

    except Exception as e:
        return jsonify([{"error": f"Veri İşleme Hatası: {str(e)}"}]), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
