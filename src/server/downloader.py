import os
import requests

# Funzione per scaricare un file audio da un URL
def scarica_segmento_audio(url, output_file):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                if os.path.getsize(output_file) > 320000:  # Limite di ~20 secondi di audio
                    break
        return True
    except Exception as e:
        print(f"Errore durante il download dell'audio da {url}: {e}")
        return False

# Funzione per mantenere solo un numero limitato di file nella directory
def mantieni_limite_file(directory, limite=4):
    try:
        files = sorted(
            [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))],
            key=lambda x: os.path.getctime(os.path.join(directory, x))
        )
        while len(files) > limite:
            file_da_eliminare = files.pop(0)
            os.remove(os.path.join(directory, file_da_eliminare))
            print(f"File eliminato: {file_da_eliminare}")
    except Exception as e:
        print(f"Errore durante la gestione dei file nella directory: {e}")
