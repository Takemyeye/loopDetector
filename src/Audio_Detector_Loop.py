import librosa
import numpy as np
import matplotlib.pyplot as plt

file_path = "audio_1.mp3"
y, sr = librosa.load(file_path, sr=None)

# Funzione per calcolare la somiglianza tra due frammenti audio
def similarity_check(segment1, segment2):
    # Utilizziamo la correlazione incrociata per confrontare i frammenti
    return np.corrcoef(segment1, segment2)[0, 1]

# Suddivisione del file audio in piccoli frammenti (ad esempio, 1 secondo)
segment_length = sr
segments = [y[i:i+segment_length] for i in range(0, len(y), segment_length)]

# Se l'ultimo frammento è più corto degli altri, lo completiamo con zeri
if len(segments[-1]) < segment_length:
    segments[-1] = np.pad(segments[-1], (0, segment_length - len(segments[-1])), 'constant')

# Cerchiamo i loop nel file audio
loop_threshold = 0.95  # Soglia di somiglianza
min_loop_duration = 10  # Durata minima del loop in secondi

loop_found = []

for i in range(len(segments)):
    for j in range(i + 1, len(segments)):
        similarity = similarity_check(segments[i], segments[j])
        
        if similarity > loop_threshold:
            # Verifichiamo che la durata del loop sia almeno di 10 secondi
            loop_duration = (j - i)  # in secondi
            if loop_duration >= min_loop_duration:
                loop_found.append((i, j, similarity))

# Mostriamo il risultato
if loop_found:
    for loop in loop_found:
        start_time = loop[0] * segment_length / sr
        end_time = loop[1] * segment_length / sr
        print(f"Loop trovato da {start_time:.2f}s a {end_time:.2f}s con somiglianza {loop[2]:.2f}")
else:
    print("Nessun loop trovato.")
