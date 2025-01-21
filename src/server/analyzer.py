import numpy as np
import librosa

# Funzione per analizzare un file audio e trovare loop usando la correlazione
def analizza_audio_per_loop(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        segment_length = sr
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

        if not loop_trovati:
            print("Nessun loop trovato con la correlazione. Passando alla ricerca dei picchi...")
            loop_trovati, y, sr = analizza_audio_per_loop_2(file_path)

        return loop_trovati, y, sr

    except Exception as e:
        print(f"Errore durante l'analisi dell'audio: {e}")
        return [], None, None


# Funzione per trovare Pichi di un segmento
def trova_pichi_nei_segmenti(y, sr, durata_segmento=1):
    campioni_segmento = int(sr * durata_segmento)
    segmenti = [y[i:i + campioni_segmento] for i in range(0, len(y), campioni_segmento)]
    
    # Se l'ultimo segmento è più corto, lo riempiamo con zeri
    if len(segmenti[-1]) < campioni_segmento:
        segmenti[-1] = np.pad(segmenti[-1], (0, campioni_segmento - len(segmenti[-1])), 'constant')
    
    # Troviamo i picchi per ogni segmento
    picchi = [np.max(np.abs(segmento)) for segmento in segmenti]
    
    return picchi, segmenti

# Secondo metodo 

# Funzione per analizzare l'audio utilizzando la ricerca dei picchi
def analizza_audio_per_loop_2(percorso_file):
    try:
        y, sr = librosa.load(percorso_file, sr=None)
        picchi, segmenti = trova_pichi_nei_segmenti(y, sr, durata_segmento=1)

        print(f"Trovati {len(picchi)} picchi.")
        
        # Logica per cercare loop, partendo da ogni picco
        gruppi_loop = []
        visitato = [False] * len(picchi)
        for i in range(len(picchi)):
            if visitato[i]:
                continue
            
            # Iniziamo un nuovo loop dal picco corrente
            gruppo_loop = [i]
            visitato[i] = True
            
            # Esploriamo i picchi successivi, verificando la distanza massima consentita
            picco_corrente = i
            while True:
                prossimo_picco = -1
                for j in range(picco_corrente + 1, len(picchi)):
                    similarita = 1 - abs(picchi[picco_corrente] - picchi[j]) / max(picchi[picco_corrente], picchi[j])
                    if similarita == 1.0 and (j - picco_corrente) <= 3:
                        prossimo_picco = j
                        break
                if prossimo_picco != -1:
                    gruppo_loop.append(prossimo_picco)
                    visitato[prossimo_picco] = True
                    picco_corrente = prossimo_picco
                else:
                    break
            
            # Se il loop consiste di più di 4 picchi, lo aggiungiamo ai risultati
            if len(gruppo_loop) > 4:
                gruppi_loop.append(gruppo_loop)

        # Se sono stati trovati dei loop, mostriamo le informazioni sull'inizio e la fine
        loop_trovati = []
        if gruppi_loop:
            print(f"Trovati {len(gruppi_loop)} loop.")
            for gruppo in gruppi_loop:
                inizio_picco = gruppo[0]
                fine_picco = gruppo[-1]
                inizio_tempo = inizio_picco / sr  # Tempo di inizio del loop in secondi
                fine_tempo = fine_picco / sr  # Tempo di fine del loop in secondi
                print(f"Il loop inizia con il picco {inizio_picco} e finisce con il picco {fine_picco}. Picchi: {gruppo}")
                loop_trovati.append((inizio_picco, fine_picco, inizio_tempo, fine_tempo))
        else:
            print("Nessun loop trovato.")
        
        return loop_trovati, y, sr

    except Exception as e:
        print(f"Errore durante l'analisi dell'audio: {e}")
        return [], None, None