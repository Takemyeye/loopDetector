import os
import soundfile as sf
from urllib.parse import urlparse
from downloader import mantieni_limite_file

# Funzione per salvare un loop trovato
def salva_loop(y, sr, start_frame, end_frame, index, url):
    try:
        loop_audio = y[start_frame:end_frame]
        parsed_url = urlparse(url)
        directory_nome = os.path.join("loops", parsed_url.netloc.replace(":", "_"))
        os.makedirs(directory_nome, exist_ok=True)

        loop_filename = os.path.join(directory_nome, f"loop_{index}.mp3")
        sf.write(loop_filename, loop_audio, sr)
        print(f"Loop salvato: {loop_filename}")

        mantieni_limite_file(directory_nome)  # Limita il numero di file nella directory
    except Exception as e:
        print(f"Errore durante il salvataggio del loop: {e}")
