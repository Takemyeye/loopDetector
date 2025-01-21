import os
import requests
from pydub import AudioSegment

def scarica_segmento_audio(url, output_file):
    try:
        # Eseguiamo la richiesta per ottenere il file audio
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Determinare l'estensione corretta del file in base al tipo di contenuto
        content_type = response.headers.get('Content-Type', '').lower()
        content_br = response.headers.get('icy-br', '')
        segment_size = int(content_br) / 8 * 20 * 1000
        file_extension = get_audio_extension(content_type)
        
        # Cambiamo il nome del file per usare l'estensione corretta
        output_file_with_extension = f"{os.path.splitext(output_file)[0]}{file_extension}"

        # Scriviamo il file scaricato con il formato corretto
        with open(output_file_with_extension, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                # Se il file supera la dimensione limite, fermiamo il download
                if os.path.getsize(output_file_with_extension) >= segment_size:
                    break
            
        # Se il file non è un mp3, lo converto in mp3
        if file_extension != '.mp3':
            convert_to_mp3(output_file_with_extension)
        
        return True
    except Exception as e:
        print(f"Errore durante il download del file da {url}: {e}")
        return False

def get_audio_extension(content_type):
    try:
        if 'audio/mpeg' in content_type:
            return '.mp3'
        elif 'audio/aac' in content_type:
            return '.aac'
        elif 'audio/wav' in content_type:
            return '.wav'
        elif 'audio/ogg' in content_type:
            return '.ogg'
        else:
            return None
    except Exception as e:
        print(f"Errore durante la determinazione dell'estensione: {e}")
        return None

def convert_to_mp3(input_file):
    try:
        mp3_file = os.path.splitext(input_file)[0] + '.mp3'
        audio = AudioSegment.from_file(input_file)
        audio.export(mp3_file, format="mp3")
        os.remove(input_file)
        
        print(f"File convertito in MP3: {mp3_file}")
    except Exception as e:
        print(f"Errore durante la conversione del file in MP3: {e}")

# Funzione per gestire i file nella directory e mantenere un limite
def mantieni_limite_file(directory, limite=4):
    try:
        # Otteniamo una lista dei file nella directory e li ordiniamo per data di creazione
        files = sorted(
            [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))],
            key=lambda x: os.path.getctime(os.path.join(directory, x))
        )
        
        # Se il numero di file supera il limite, rimuoviamo i più vecchi
        while len(files) > limite:
            file_to_delete = files.pop(0)
            os.remove(os.path.join(directory, file_to_delete))
            print(f"File eliminato: {file_to_delete}")
    except Exception as e:
        print(f"Errore durante la gestione dei file nella directory: {e}")
