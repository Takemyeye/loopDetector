import numpy as np
import librosa

# Funzione per analizzare un file audio e trovare loop
def analizza_audio_per_loop(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        segment_length = sr  # Segmenti di 1 secondo
        segments = [y[i:i + segment_length] for i in range(0, len(y), segment_length)]

        if len(segments[-1]) < segment_length:
            segments[-1] = np.pad(segments[-1], (0, segment_length - len(segments[-1])), 'constant')

        soglia_loop = 0.94  # Soglia di similarità
        durata_minima_loop = 8  # Durata minima del loop in secondi
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
