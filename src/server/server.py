import requests
import librosa
import numpy as np
import soundfile as sf
import os
import threading
import time
from flask import Flask, request, jsonify

# Configurazione
url = "http://audio1.meway.tv:8099/live"
output_file = "downloaded_audio_20s.mp3"
loop_directory = "loops"
post_url = "http://localhost:3001/api/messages"

# Creazione directory per i loop
if not os.path.exists(loop_directory):
    os.makedirs(loop_directory)

# Funzione per scaricare un segmento audio
def scarica_segmento_audio(url, output_file):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                if os.path.getsize(output_file) > 380000:  # Circa 20 secondi di audio
                    break
        return True
    except Exception as e:
        print(f"Errore durante il download dell'audio: {e}")
        return False

# Funzione per analizzare l'audio e identificare i loop
def analizza_audio_per_loop(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        segment_length = sr
        segments = [y[i:i + segment_length] for i in range(0, len(y), segment_length)]

        if len(segments[-1]) < segment_length:
            segments[-1] = np.pad(segments[-1], (0, segment_length - len(segments[-1])), 'constant')

        soglia_loop = 0.94
        durata_minima_loop = 7
        loop_trovati = []

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

# Funzione per salvare i loop trovati
def salva_loop(y, sr, start_frame, end_frame, index):
    try:
        loop_audio = y[start_frame:end_frame]
        loop_filename = os.path.join(loop_directory, f"loop_{index}.wav")
        sf.write(loop_filename, loop_audio, sr)
        print(f"Loop salvato: {loop_filename}")
    except Exception as e:
        print(f"Errore durante il salvataggio del loop: {e}")

# Funzione per analizzare l'audio e inviare i risultati al server
def analyze_and_send():
    loop_index = 0

    while True:
        if scarica_segmento_audio(url, output_file):
            loops, y, sr = analizza_audio_per_loop(output_file)

            if loops:
                message = {"status": "loop_found", "loops": []}
                print("Loop trovato!")

                for l in loops:
                    tempo_inizio = l[0] * sr
                    tempo_fine = l[1] * sr
                    similarita = l[2]
                    print(f"Loop: {tempo_inizio / sr:.2f}s - {tempo_fine / sr:.2f}s (somiglianza: {similarita:.2f})")

                    salva_loop(y, sr, int(tempo_inizio), int(tempo_fine), loop_index)
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
                try:
                    response = requests.post(post_url, json={"status": "no_loop"})
                    print(f"Risposta del server: {response.status_code} - {response.text}")
                except Exception as e:
                    print(f"Errore durante l'invio dei dati: {e}")

            os.remove(output_file)

        time.sleep(5)

# Server Flask per ricevere i dati
app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_data():
    """
    Endpoint per ricevere i dati del loop.
    """
    data = request.json
    print(f"Dati ricevuti: {data}")
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # Avvio del thread per analizzare e inviare i dati
    server_thread = threading.Thread(target=analyze_and_send, daemon=True)
    server_thread.start()

    # Avvio del server Flask
    porta = 3002
    print(f"Server Flask avviato sulla porta {porta}. Premere Ctrl+C per uscire.")
    try:
        app.run(port=porta)
    except KeyboardInterrupt:
        print("Server arrestato.")
