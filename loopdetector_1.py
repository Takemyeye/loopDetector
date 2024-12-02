import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def detect_dynamic_loops(y, sr, segment_length=2, similarity_threshold=0.5, min_distance=2.0, sub_segment_length=0.5):
    """
    Rileva frammenti ripetuti nell'audio utilizzando sotto-frammenti per migliorare la precisione.
    - y: segnale audio
    - sr: frequenza di campionamento
    - segment_length: lunghezza del segmento in secondi
    - similarity_threshold: soglia di somiglianza
    - min_distance: distanza minima tra le aree ripetute (in secondi)
    - sub_segment_length: lunghezza del sotto-frammento per il confronto
    """
    segment_samples = segment_length * sr  # Lunghezza del segmento in campioni
    sub_segment_samples = sub_segment_length * sr  # Lunghezza del sotto-frammento in campioni
    num_segments = len(y) // segment_samples  # Numero di segmenti

    loops = []

    # Estrazione MFCC (è possibile utilizzare anche altre caratteristiche)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    # Rendi tutti i frammenti della stessa lunghezza in termini di frame
    target_length = mfcc.shape[1]  # Lunghezza del primo frammento in frame

    # Interpolazione per allineare le dimensioni
    def interpolate_mfcc(mfcc_segment, target_length):
        current_length = mfcc_segment.shape[1]
        # Interpolazione
        interpolator = interp1d(np.linspace(0, current_length, current_length), mfcc_segment, axis=1, fill_value="extrapolate")
        return interpolator(np.linspace(0, current_length, target_length))

    for i in range(num_segments):
        # Estrai il frammento corrente
        segment1_mfcc = mfcc[:, i * segment_samples // 512: (i + 1) * segment_samples // 512]
        segment1_mfcc = interpolate_mfcc(segment1_mfcc, target_length)

        # Dividi in sotto-frammenti
        sub_fragments1 = [segment1_mfcc[:, int(sub_i * sub_segment_samples // 512): int((sub_i + 1) * sub_segment_samples // 512)] 
                          for sub_i in range(int(len(segment1_mfcc[0]) / sub_segment_samples))]

        # Confronta con altri frammenti
        for j in range(i + 1, num_segments):
            segment2_mfcc = mfcc[:, j * segment_samples // 512: (j + 1) * segment_samples // 512]
            segment2_mfcc = interpolate_mfcc(segment2_mfcc, target_length)

            # Dividi in sotto-frammenti
            sub_fragments2 = [segment2_mfcc[:, int(sub_k * sub_segment_samples // 512): int((sub_k + 1) * sub_segment_samples // 512)] 
                              for sub_k in range(int(len(segment2_mfcc[0]) / sub_segment_samples))]

            # Confronta i sotto-frammenti
            for sub1 in sub_fragments1:
                for sub2 in sub_fragments2:
                    # Somiglianza del coseno tra i sotto-frammenti
                    similarity = np.dot(sub1.flatten(), sub2.flatten()) / (np.linalg.norm(sub1.flatten()) * np.linalg.norm(sub2.flatten()))

                    if similarity > similarity_threshold:
                        t1 = i * segment_length
                        t2 = j * segment_length
                        if abs(t2 - t1) > min_distance:
                            loops.append((t1, t2, similarity))

    return loops

# Caricamento audio
file_path = "downloaded_audio_30s.mp3"
y, sr = librosa.load(file_path, sr=None)

# Ricerca di loop dinamici
loops = detect_dynamic_loops(y, sr, segment_length=2, similarity_threshold=0.5, min_distance=1.0, sub_segment_length=0.5)

# Visualizzazione dei risultati
if loops:
    print("Aree ripetute trovate:")
    for t1, t2, similarity in loops:
        print(f"Frammento 1: {t1:.2f} sec, Frammento 2: {t2:.2f} sec, Somiglianza: {similarity:.2f}")
else:
    print("Aree ripetute non trovate.")

# Visualizzazione
plt.figure(figsize=(12, 8))
librosa.display.waveshow(y, sr=sr)
plt.title("Forma d'onda dell'audio")
plt.xlabel("Tempo (secondi)")
plt.ylabel("Ampiezza")
plt.grid()
plt.show()
