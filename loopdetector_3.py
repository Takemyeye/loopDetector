import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def detect_loops_full_scan(y, sr, segment_length=2, sub_segment_length=0.5, similarity_threshold=0.5, min_distance=2.0):
    """
    Поиск повторяющихся фрагментов в аудиофайле без предварительных знаний о местоположении.
    - y: сигнал аудио
    - sr: частота дискретизации
    - segment_length: длина сегмента (в секундах)
    - sub_segment_length: длина подфрагмента (в секундах)
    - similarity_threshold: порог сходства
    - min_distance: минимальная дистанция между совпадающими сегментами (в секундах)
    """
    segment_samples = int(segment_length * sr)  # Длина сегмента в отсчётах
    sub_segment_samples = int(sub_segment_length * sr)  # Длина подфрагмента в отсчётах
    num_segments = len(y) // segment_samples  # Общее число сегментов

    loops = []  # Список найденных лупов
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # Извлечение MFCC

    # Интерполяция для выравнивания по длине
    def interpolate_mfcc(mfcc_segment, target_length):
        current_length = mfcc_segment.shape[1]
        interpolator = interp1d(np.linspace(0, current_length, current_length), mfcc_segment, axis=1, fill_value="extrapolate")
        return interpolator(np.linspace(0, current_length, target_length))

    # Основной цикл для поиска лупов
    for i in range(num_segments):
        segment1_start = i * segment_samples
        segment1_end = segment1_start + segment_samples
        segment1_mfcc = mfcc[:, segment1_start // 512: segment1_end // 512]

        # Уточнение через подфрагменты
        for j in range(i + 1, num_segments):
            segment2_start = j * segment_samples
            segment2_end = segment2_start + segment_samples
            segment2_mfcc = mfcc[:, segment2_start // 512: segment2_end // 512]

            # Проверка подфрагментов
            for sub_start1 in range(0, segment1_mfcc.shape[1] - sub_segment_samples // 512, sub_segment_samples // 512):
                sub1 = segment1_mfcc[:, sub_start1:sub_start1 + sub_segment_samples // 512]
                for sub_start2 in range(0, segment2_mfcc.shape[1] - sub_segment_samples // 512, sub_segment_samples // 512):
                    sub2 = segment2_mfcc[:, sub_start2:sub_start2 + sub_segment_samples // 512]

                    # Вычисление сходства
                    similarity = np.dot(sub1.flatten(), sub2.flatten()) / (np.linalg.norm(sub1.flatten()) * np.linalg.norm(sub2.flatten()))
                    if similarity > similarity_threshold:
                        t1 = segment1_start / sr
                        t2 = segment2_start / sr
                        if abs(t2 - t1) > min_distance:
                            loops.append((t1, t2, similarity))

    return loops

# Загрузка аудиофайла
file_path = "downloaded_audio_30s.mp3"
y, sr = librosa.load(file_path, sr=None)

# Запуск поиска лупов
loops = detect_loops_full_scan(y, sr, segment_length=2, sub_segment_length=0.5, similarity_threshold=0.5, min_distance=1.0)

# Вывод всех сходств
if loops:
    print("Найденные лупы (сходства):")
    
    streaks = []
    current_streak = []
    
    # Вывод всех сходств
    for t1, t2, similarity in loops:
        print(f"Начало 1: {t1:.2f} сек, Начало 2: {t2:.2f} сек, Сходство: {similarity:.2f}")
        
        # Формируем стрики
        if similarity >= 0.90:
            if not current_streak:
                current_streak.append((t1, t2))
            else:
                # Если текущий луп рядом с предыдущим по времени (в пределах min_distance)
                last_t2 = current_streak[-1][1]
                if t1 - last_t2 <= 2.0:  # min_distance
                    current_streak.append((t1, t2))
                else:
                    streaks.append(current_streak)
                    current_streak = [(t1, t2)]
        else:
            if current_streak:
                streaks.append(current_streak)
            current_streak = []

    # Добавляем последний стрик, если он существует
    if current_streak:
        streaks.append(current_streak)

    # Фильтрация стриков по длительности (больше 10 секунд)
    valid_loops = []
    for streak in streaks:
        start_time = streak[0][0]
        end_time = streak[-1][1]
        duration = end_time - start_time
        if duration >= 10.0:  # Луп должен быть 10 секунд или больше
            valid_loops.append((start_time, end_time, duration))

    # Выводим самый длинный луп (если он есть)
    if valid_loops:
        # Сортируем по длительности и выбираем самый длинный
        longest_loop = max(valid_loops, key=lambda x: x[2])
        print(f"\nСамый длинный луп: Начало: {longest_loop[0]:.2f} сек, Конец: {longest_loop[1]:.2f} сек, Длительность: {longest_loop[2]:.2f} сек")
    else:
        print("\nНет лупов длительностью 10 секунд и больше.")
else:
    print("Повторяющиеся области не найдены.")

# Построение графика для визуализации
plt.figure(figsize=(12, 6))
librosa.display.waveshow(y, sr=sr)
plt.title("Аудиофайл: форма волны")
plt.xlabel("Время (секунды)")
plt.ylabel("Амплитуда")
plt.grid()
plt.show()
