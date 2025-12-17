from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# MKOSZ Pest Bölgesi Linkleri (A, B, C Grupları)
GROUPS = [
    {"name": "Grup A", "url": "https://megye.hunbasket.hu/pest/bajnoksag/x2526/hun_pes_rfj/9789"},
    {"name": "Grup B", "url": "https://megye.hunbasket.hu/pest/bajnoksag/x2526/hun_pes_rfj/9800"},
    {"name": "Grup C", "url": "https://megye.hunbasket.hu/pest/bajnoksag/x2526/hun_pes_rfj/9801"}
]

@app.route('/', methods=['GET'])
def home():
    return "MKOSZ API Calisiyor! Veriler icin /maclar adresine git."

@app.route('/maclar', methods=['GET'])
def get_data():
    all_matches = []
    match_id = 1
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for group in GROUPS:
        try:
            # Siteye baglan
            r = requests.get(group['url'], headers=headers)
            r.encoding = 'utf-8' # Karakter sorunu icin
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Tablo satirlarini bul
            rows = soup.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                # Bir satirda yeterli sutun varsa ve icinde tarih varsa mac satiridir
                if len(cols) >= 4:
                    texts = [c.get_text(strip=True) for c in cols]
                    
                    # Tarih kontrolu (Sayi iceriyor mu?)
                    if len(texts) > 0 and any(char.isdigit() for char in texts[0]):
                        
                        # Varsayilan degerler
                        match_data = {
                            "id": match_id,
                            "group": group['name'],
                            "date": texts[0],
                            "home": "Bilinmiyor",
                            "away": "Bilinmiyor",
                            "score": "v", 
                            "status": "MS"
                        }

                        # Sitenin yapisina gore sutunlari esle
                        # Genelde: 0:Tarih, 1:Saat, 2:Ev, 3:Skor, 4:Dep
                        if len(texts) >= 5:
                            match_data["home"] = texts[2]
                            match_data["score"] = texts[3]
                            match_data["away"] = texts[4]
                            
                            # Eger skor yoksa mac oynanmamistir
                            if match_data["score"] == "" or match_data["score"] == "-":
                                match_data["score"] = "v"
                                match_data["status"] = texts[1] # Saati durum yap
                        
                        # Alternatif yapi (Saat yoksa): 0:Tarih, 1:Ev, 2:Skor, 3:Dep
                        elif len(texts) == 4:
                             match_data["home"] = texts[1]
                             match_data["score"] = texts[2]
                             match_data["away"] = texts[3]

                        # Takim isimleri doluysa listeye ekle
                        if len(match_data["home"]) > 1:
                            all_matches.append(match_data)
                            match_id += 1

        except Exception as e:
            print(f"Hata ({group['name']}): {e}")
            
    return jsonify(all_matches)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
