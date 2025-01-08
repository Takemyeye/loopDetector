from flask import Flask, request, jsonify
from urllib.parse import urlparse
import soundfile as sf
import numpy as np
import threading
import requests
import librosa
import time
import os

# Directory principale per i file audio e i loop
output_directory = "downloads"
loop_base_directory = "loops"
post_url = "http://localhost:3001/api/messages"

# Creazione delle directory se non esistono
os.makedirs(output_directory, exist_ok=True)
os.makedirs(loop_base_directory, exist_ok=True)

# Funzione per scaricare un segmento audio da un URL
def scarica_segmento_audio(url, output_file):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                if os.path.getsize(output_file) > 320000:  # Limite di circa 20 secondi di audio
                    break
        return True
    except Exception as e:
        print(f"Errore durante il download dell'audio da {url}: {e}")
        return False

# Funzione per analizzare il file audio e identificare i loop
def analizza_audio_per_loop(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        segment_length = sr  # Segmento di 1 secondo
        segments = [y[i:i + segment_length] for i in range(0, len(y), segment_length)]

        # Padding dell'ultimo segmento se non è completo
        if len(segments[-1]) < segment_length:
            segments[-1] = np.pad(segments[-1], (0, segment_length - len(segments[-1])), 'constant')

        soglia_loop = 0.94  # somiglianza
        durata_minima_loop = 8  # Durata minima in secondi
        loop_trovati = []

        # Confronto dei segmenti per identificare i loop
        for i in range(len(segments)):
            for j in range(i + 1, len(segments)):
                similarita = np.corrcoef(segments[i], segments[j])[0, 1]
                if similarita > soglia_loop:
                    durata_loop = (j - i)
                    if durata_loop >= durata_minima_loop:
                        loop_trovati.append((i, j, similarita))

        return loop_trovati, y, sr
    except Exception as e:
        print(f"Errore durante l'analisi dell'audio: {e}")
        return [], None, None

# Funzione per mantenere solo 4 file nella directory
def mantieni_limite_file(directory, limite=4):
    try:
        files = sorted([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))], key=lambda x: os.path.getctime(os.path.join(directory, x)))
        while len(files) > limite:
            file_da_eliminare = files.pop(0)
            os.remove(os.path.join(directory, file_da_eliminare))
            print(f"File eliminato: {file_da_eliminare}")
    except Exception as e:
        print(f"Errore durante la gestione dei file nella directory: {e}")

# Funzione per salvare un loop trovato in una directory specifica per URL
def salva_loop(y, sr, start_frame, end_frame, index, url):
    try:
        loop_audio = y[start_frame:end_frame]
        parsed_url = urlparse(url)
        directory_nome = os.path.join(loop_base_directory, parsed_url.netloc.replace(":", "_"))
        os.makedirs(directory_nome, exist_ok=True)

        loop_filename = os.path.join(directory_nome, f"loop_{index}.mp3")
        sf.write(loop_filename, loop_audio, sr)
        print(f"Loop salvato: {loop_filename}")

        # Mantieni solo i 4 file più recenti nella directory
        mantieni_limite_file(directory_nome)
    except Exception as e:
        print(f"Errore durante il salvataggio del loop: {e}")

# Funzione per analizzare i dati e inviarli al server
def analyze_and_send(url, url_index):
    loop_index = 0
    output_file = os.path.join(output_directory, f"audio_{url_index}.mp3")

    while True:
        if scarica_segmento_audio(url, output_file):
            loops, y, sr = analizza_audio_per_loop(output_file)
            if loops:
                message = {"status": True, "url": url, "loops": []}

                for l in loops:
                    tempo_inizio = l[0] * sr
                    tempo_fine = l[1] * sr
                    similarita = l[2]
                    print(f"Loop trovato su {url}: {tempo_inizio / sr:.2f}s - {tempo_fine / sr:.2f}s (somiglianza: {similarita:.2f})")

                    salva_loop(y, sr, int(tempo_inizio), int(tempo_fine), loop_index, url)
                    loop_index += 1

                    message["loops"].append({
                        "start": tempo_inizio / sr,
                        "end": tempo_fine / sr,
                        "similarity": similarita
                    })

                try:
                    response = requests.post(post_url, json=message)
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

# Creazione del server Flask per ricevere i dati
app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_data():
    data = request.json
    print(f"Dati ricevuti: {data}")
    return jsonify({"status": "ok"})

# Avvio dell'analisi e del server Flask
if __name__ == "__main__":
    try:
        # Fai richiesta per ottenere gli URL dal server Node.js
        response = requests.get("http://localhost:3001/api/streams")
        urls = response.json().get('streams', [])
        print("URL ricevuti dal server:", urls)

        # Avvia i thread per ogni URL ricevuto
        for idx, url in enumerate(urls):
            threading.Thread(target=analyze_and_send, args=(url, idx), daemon=True).start()

        # Avvia il server Flask
        porta = 3002
        print(f"Server Flask avviato sulla porta {porta}. Premere Ctrl+C per uscire.")
        app.run(port=porta)
    except KeyboardInterrupt:
        print("Server arrestato.")
    except Exception as e:
        print(f"Errore durante l'avvio del server: {e}")
