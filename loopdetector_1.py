import librosa
import numpy as np

def detect_loop(audio_file, sr=44100, threshold=0.8):

    y, sr = librosa.load(audio_file, sr=sr)

    signal_length = len(y)

    window_size = sr 

    for loop_length in range(window_size, signal_length // 2, window_size):
        loop = y[-loop_length:]
        
        start_position = signal_length - 2 * loop_length
        if start_position < 0:
            break
        
        segment_to_compare = y[start_position : start_position + loop_length]
        
        correlation = np.corrcoef(loop, segment_to_compare)[0, 1]
        
        if correlation >= threshold:
            print(f"Loop detected! Start: {start_position / sr:.2f} seconds, Length: {loop_length / sr:.2f} seconds")
            return start_position, loop_length

    print("No loop detected.")
    return None

audio_file = "test2.mp3"
detect_loop(audio_file)
