import librosa
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def generate_random_color():
    """Генерирует случайный цвет."""
    return np.random.rand(3,)

def find_peaks_in_segments(y, sr, segment_duration=1):
    """Нарезает аудио на сегменты и находит пики в каждом сегменте."""
    segment_samples = int(sr * segment_duration)
    segments = [y[i:i + segment_samples] for i in range(0, len(y), segment_samples)]
    
    # Если последний сегмент короче, заполняем его нулями
    if len(segments[-1]) < segment_samples:
        segments[-1] = np.pad(segments[-1], (0, segment_samples - len(segments[-1])), 'constant')
    
    # Находим пики для каждого сегмента
    peaks = [np.max(np.abs(segment)) for segment in segments]
    
    return peaks, segments

def compare_segments(segment_a, segment_b):
    """Вычисление схожести между двумя сегментами с использованием косинусного сходства."""
    segment_a = segment_a / np.linalg.norm(segment_a)
    segment_b = segment_b / np.linalg.norm(segment_b)
    similarity = cosine_similarity([segment_a], [segment_b])
    return similarity[0][0]

def segment_audio_for_loop(audio_file, segment_duration=1, similarity_threshold=0.90, peak_similarity_threshold=0.95, max_gap=3):
    """Нарезает аудиофайл и ищет лупы между пиками с допустимой погрешностью по сегментам."""
    # Загружаем аудиофайл
    print(f"Загружается файл: {audio_file}")
    y, sr = librosa.load(audio_file, sr=None)
    
    # Разбиваем аудио на сегменты и находим пики
    peaks, segments = find_peaks_in_segments(y, sr, segment_duration)
    
    print(f"Найдено {len(peaks)} пиков.")
    
    # Сравниваем пики, которые расположены через одинаковое расстояние или похожи на 100%
    similar_peaks = []
    for i in range(len(peaks) - 1):
        for j in range(i + 1, len(peaks)):
            similarity = 1 - abs(peaks[i] - peaks[j]) / max(peaks[i], peaks[j])
            if similarity == 1.0:  # Только 100%-ная схожесть
                similar_peaks.append((i, j))
    
    print("Найденные пики с 100%-ной схожестью:", similar_peaks)

    # Логика поиска лупов, начиная с каждого пика
    loop_groups = []
    visited = [False] * len(peaks)  # Массив для отслеживания, какие пики уже были включены в луп
    for i in range(len(peaks)):
        if visited[i]:
            continue
        
        # Старт нового лупа с текущего пика
        loop_group = [i]
        visited[i] = True
        
        # Перебор следующих пиков с 100%-ной схожестью, проверяем макс. допустимое расстояние
        current_peak = i
        while True:
            next_peak = -1
            for j in range(current_peak + 1, len(peaks)):
                similarity = 1 - abs(peaks[current_peak] - peaks[j]) / max(peaks[current_peak], peaks[j])
                if similarity == 1.0 and (j - current_peak) <= max_gap:
                    next_peak = j
                    break
            if next_peak != -1:
                loop_group.append(next_peak)
                visited[next_peak] = True
                current_peak = next_peak
            else:
                break
        
        # Если луп состоит более чем из 4 пиков, добавляем его в результат
        if len(loop_group) > 4:
            loop_groups.append(loop_group)

    # Если нашли хотя бы один луп, выводим информацию о времени начала и конце
    if loop_groups:
        print(f"Найдено лупов: {len(loop_groups)}")
        for group in loop_groups:
            start_peak = group[0]
            end_peak = group[-1]
            start_time = start_peak / sr  # Время начала лупа в секундах
            end_time = end_peak / sr  # Время конца лупа в секундах
            print(f"Луп начинается с пика {start_peak} ({start_time:.2f} сек.) и заканчивается пиком {end_peak} ({end_time:.2f} сек.). Пики: {group}")
    else:
        print("Лупы не найдены.")

# Пример использования
audio_file = 'audio_1.mp3'  # Укажите путь к вашему файлу
segment_audio_for_loop(audio_file)
