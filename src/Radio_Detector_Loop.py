import requests
import librosa
import numpy as np
import soundfile as sf
import os

# URL dell'audio
url = "http://audio1.meway.tv:8099/live"
output_file = "downloaded_audio_20s.mp3"
loop_directory = "loops"  # Cartella per salvare i loop

# Creazione della cartella per i loop, se non esiste
if not os.path.exists(loop_directory):
    os.makedirs(loop_directory)

# Funzione per scaricare 20 secondi di audio
def scarica_segmento_audio(url, output_file):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                # Circa 440000 byte per 20 secondi di MP3 a 128 kbps
                if os.path.getsize(output_file) > 380000:
                    break
        return True
    except Exception as e:
        print(f"Errore durante il download dell'audio: {e}")
        return False

# Funzione per analizzare i loop
def analizza_audio_per_loop(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        segment_length = sr
        segments = [y[i:i + segment_length] for i in range(0, len(y), segment_length)]
        
        if len(segments[-1]) < segment_length:
            segments[-1] = np.pad(segments[-1], (0, segment_length - len(segments[-1])), 'constant')
        
        soglia_loop = 0.90
        durata_minima_loop = 10  # in secondi
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
        sf.write(loop_filename, loop_audio, sr)  # Utilizza soundfile per salvare il file
        print(f"Loop salvato: {loop_filename}")
    except Exception as e:
        print(f"Errore durante il salvataggio del loop: {e}")

# Ciclo infinito principale
last_loop_active = False
last_loop_time = None
loop_index = 0  # Indice per i nomi dei file dei loop

try:
    while True:
        # Scarichiamo un nuovo segmento
        if scarica_segmento_audio(url, output_file):
            # Analizziamo il file per verificare la presenza di loop
            loops, y, sr = analizza_audio_per_loop(output_file)
            
            if loops:
                if not last_loop_active:
                    print("Loop trovato!")
                last_loop_active = True
                
                for l in loops:
                    tempo_inizio = l[0] * sr
                    tempo_fine = l[1] * sr
                    similarita = l[2]
                    print(f"Loop: {tempo_inizio / sr:.2f}s - {tempo_fine / sr:.2f}s (similarità: {similarita:.2f})")
                    
                    # Salviamo il loop corrente
                    salva_loop(y, sr, int(tempo_inizio), int(tempo_fine), loop_index)
                    loop_index += 1
                
                # Salviamo l'ultimo intervallo temporale
                last_loop_time = loops[-1][1] * sr
            else:
                # Se non ci sono loop in questo segmento
                if last_loop_active:
                    if last_loop_time and last_loop_time >= len(y):
                        print("Loop continua nel prossimo file...")
                    else:
                        print("Loop terminato.")
                        last_loop_active = False
            
            # Eliminiamo il file temporaneo
            os.remove(output_file)

except KeyboardInterrupt:
    print("Script terminato dall'utente.")
