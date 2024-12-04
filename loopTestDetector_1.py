import requests
import librosa
import numpy as np
import time

# Функция для получения аудио потока с URL
def get_audio_stream(url):
    response = requests.get(url, stream=True)
    return response.content

# Функция для анализа аудио потока и поиска лупа
def analyze_loop(audio_data, window_size=10, tolerance=5):
    # Преобразуем аудио данные в формат, который можно обработать
    y, sr = librosa.load(audio_data, sr=None)
    
    # Разбиваем на 10 секундные фрагменты
    segment_length = window_size * sr
    num_segments = len(y) // segment_length
    
    previous_segment = None
    
    for i in range(num_segments):
        start = i * segment_length
        end = (i + 1) * segment_length
        current_segment = y[start:end]
        
        if previous_segment is not None:
            # Проверяем, если текущий сегмент схож с предыдущим
            correlation = np.corrcoef(previous_segment, current_segment)[0, 1]
            
            # Если схожесть выше порогового значения, это может быть луп
            if correlation > 0.95:  # Можно адаптировать порог
                print(f"Loop detected at {i * window_size} seconds.")
        
        previous_segment = current_segment
        
        # Пауза для имитации реального времени
        time.sleep(tolerance)

# Получаем аудио поток
url = "http://audio1.meway.tv:8099/live"
audio_data = get_audio_stream(url)

# Анализируем на лупы
analyze_loop(audio_data)
