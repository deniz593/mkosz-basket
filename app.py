from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# Linkler (A, B, C Grupları)
GROUPS = [
    {"name": "Grup A", "url": "https://megye.hunbasket.hu/pest/bajnoksag/x2526/hun_pes_rfj/9789"},
    {"name": "Grup B", "url": "https://megye.hunbasket.hu/pest/bajnoksag/x2526/hun_pes_rfj/9800"},
    {"name": "Grup C", "url": "https://megye.hunbasket.hu/pest/bajnoksag/x2526/hun_pes_rfj/9801"}
]

@app.route('/', methods=['GET'])
def home():
    return "Sunucu Calisiyor!"

@app.route('/maclar', methods=['GET'])
def get_data():
    all_matches = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for group in GROUPS:
        try:
            resp = requests.get(group['url'], headers=headers)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            rows = soup.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    # Basit veri çekme
                    tarih = cols[0].get_text(strip=True)
                    ev = cols[2].get_text(strip=True)
                    skor = cols[3].get_text(strip=True)
                    dep = cols[4].get_text(strip=True)
                    
                    if "202" in tarih: # Tarih içeriyorsa al
                        status = "MS"
                        if skor == "" or skor == "-": 
                            skor = "v"
                            status = cols[1].get_text(strip=True)
                        
                        all_matches.append({
                            "group": group['name'],
                            "home": ev, "away": dep, 
                            "score": skor, "status": status, "date": tarih
                        })
        except: pass
    return jsonify(all_matches)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)