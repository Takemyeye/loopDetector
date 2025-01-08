from flask import Flask, request, jsonify
import threading
import requests
import time
import os

from downloader import scarica_segmento_audio
from analyzer import analizza_audio_per_loop
from saver import salva_loop

# Configurazione
output_directory = "downloads"
post_url = "http://localhost:3001/api/messages"
os.makedirs(output_directory, exist_ok=True)

# Funzione per analizzare e inviare dati
def analizza_e_invia(url, url_index):
    loop_index = 0
    output_file = os.path.join(output_directory, f"audio_{url_index}.mp3")

    while True:
        if scarica_segmento_audio(url, output_file):
            loops, y, sr = analizza_audio_per_loop(output_file)
            if loops:
                messaggio = {"status": True, "url": url, "loops": []}
                for l in loops:
                    tempo_inizio = l[0] * sr
                    tempo_fine = l[1] * sr
                    similarita = l[2]
                    print(f"Loop trovato su {url}: {tempo_inizio / sr:.2f}s - {tempo_fine / sr:.2f}s (similarità: {similarita:.2f})")

                    salva_loop(y, sr, int(tempo_inizio), int(tempo_fine), loop_index, url)
                    loop_index += 1

                    messaggio["loops"].append({
                        "start": tempo_inizio / sr,
                        "end": tempo_fine / sr,
                        "similarity": similarita
                    })

                try:
                    response = requests.post(post_url, json=messaggio)
                    print(f"Risposta del server: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"Errore durante l'invio dei dati: {e}")
            else:
                print(f"Loop non trovato su {url}.")
                try:
                    response = requests.post(post_url, json={"status": False, "url": url})
                    print(f"Risposta del server: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"Errore durante l'invio dei dati: {e}")
            os.remove(output_file)
        time.sleep(5)

# Creazione del server Flask
app = Flask(__name__)

@app.route('/', methods=['POST'])
def ricevi_dati():
    data = request.json
    print(f"Dati ricevuti: {data}")
    return jsonify({"status": "ok"})

# Avvio del server e analisi
if __name__ == "__main__":
    try:
        response = requests.get("http://localhost:3001/api/streams")
        urls = response.json().get('streams', [])
        print("URL ricevuti dal server:", urls)

        for idx, url in enumerate(urls):
            threading.Thread(target=analizza_e_invia, args=(url, idx), daemon=True).start()

        porta = 3002
        print(f"Server Flask avviato sulla porta {porta}. Premere Ctrl+C per uscire.")
        app.run(port=porta)
    except KeyboardInterrupt:
        print("Server arrestato.")
    except Exception as e:
        print(f"Errore durante l'avvio del server: {e}")
