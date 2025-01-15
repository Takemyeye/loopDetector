from flask import Flask, request, jsonify
import threading
import requests
import time
import os
import logging
import psutil

from downloader import scarica_segmento_audio
from analyzer import analizza_audio_per_loop
from saver import salva_loop

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurazione
output_directory = "downloads"
post_url = "http://localhost:3004/api/messages"
os.makedirs(output_directory, exist_ok=True)

# Memorizziamo lo stato dei flussi e i thread attivi
streams_state = {}

# Funzione per analizzare e inviare i dati
def analizza_e_invia(url, id, url_index, stop_event):
    try:
        loop_index = 0
        output_file = os.path.join(output_directory, f"audio_{url_index}.mp3")

        while not stop_event.is_set():  # Verifica se il thread deve fermarsi
            if scarica_segmento_audio(url, output_file):
                loops, y, sr = analizza_audio_per_loop(output_file)
                if loops:
                    messaggio = {"status_loop": True, "url": url, "id": id, "loops": []}
                    for l in loops:
                        tempo_inizio = l[0] * sr
                        tempo_fine = l[1] * sr
                        similarita = l[2]
                        logging.info(f"Loop trovato su {url}: {tempo_inizio / sr:.2f}s - {tempo_fine / sr:.2f}s (similarità: {similarita:.2f})")

                        salva_loop(y, sr, int(tempo_inizio), int(tempo_fine), loop_index, url)
                        loop_index += 1

                        messaggio["loops"].append({
                            "start": tempo_inizio / sr,
                            "end": tempo_fine / sr,
                            "similarity": similarita
                        })

                    try:
                        response = requests.post(post_url, json=messaggio)
                        logging.info(f"Risposta del server: {response.status_code} - {response.text}")
                    except Exception as e:
                        logging.error(f"Errore durante l'invio dei dati: {e}")
                else:
                    logging.info(f"Loop non trovato su {url}.")
                    try:
                        response = requests.post(post_url, json={"status_loop": False, "url": url, "id": id})
                        logging.info(f"Risposta del server: {response.status_code} - {response.text}")
                    except Exception as e:
                        logging.error(f"Errore durante l'invio dei dati: {e}")
                os.remove(output_file)
            time.sleep(3)
    except Exception as e:
        logging.error(f"Errore nel thread per {url}: {e}")

# Funzione per verificare e gestire i flussi attivi
def verifica_streams_e_lup():
    try:
        response = requests.get("http://localhost:3004/api/streams")
        urls = response.json().get('streams', [])
        logging.info(f"URL ricevuti dal server: {urls}")

        for idx, url_obj in enumerate(urls):
            id = url_obj.get('id', '')
            url = url_obj.get('url', '')
            status = url_obj['status']

            if id in streams_state:
                old_status, stop_event = streams_state[id]
                if old_status != status:
                    if not status:
                        # Se lo stato è cambiato a False, fermiamo immediatamente il processo
                        logging.info(f"Status cambiato a False per {id}, terminazione immediata del processo.")
                        stop_event.set()
                        del streams_state[id]
                    elif status:
                        logging.info(f"Status cambiato a True per {id}, riavviamo l'analisi.")
                        stop_event.clear()
                        t = threading.Thread(target=analizza_e_invia, args=(url, id, idx, stop_event), daemon=True)
                        t.start()
                        streams_state[id] = (status, stop_event, t.ident)
            else:
                if status:
                    logging.info(f"Nuovo flusso {id} attivo, avviamo l'analisi.")
                    stop_event = threading.Event()
                    t = threading.Thread(target=analizza_e_invia, args=(url, id, idx, stop_event), daemon=True)
                    t.start()
                    streams_state[id] = (status, stop_event, t.ident)

    except Exception as e:
        logging.error(f"Errore durante la verifica dei flussi: {e}")

# Funzione periodica per controllare i flussi
def verifica_periodicamente():
    while True:
        verifica_streams_e_lup()
        time.sleep(6000)

# Creazione del server Flask
app = Flask(__name__)

@app.route('/', methods=['POST'])
def ricevi_dati():
    try:
        data = request.json
        if not data or "status" not in data or "id" not in data or "url" not in data:
            return jsonify({"status": "error", "message": "Formato dati non valido"}), 400
        
        logging.info(f"Dati ricevuti: {data}")
        
        threading.Thread(target=verifica_streams_e_lup, daemon=True).start()
        
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Avvio del server e analisi
if __name__ == "__main__":
    try:
        threading.Thread(target=verifica_periodicamente, daemon=True).start()

        porta = 3002
        logging.info(f"Server Flask avviato sulla porta {porta}. Premere Ctrl+C per uscire.")
        app.run(port=porta)
    except KeyboardInterrupt:
        logging.info("Server arrestato.")
    except Exception as e:
        logging.error(f"Errore durante l'avvio del server: {e}")
