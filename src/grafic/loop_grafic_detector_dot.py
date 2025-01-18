import librosa
import numpy as np
import matplotlib.pyplot as plt
import random

def generate_random_color():
    """Генерирует случайный цвет."""
    return (random.random(), random.random(), random.random())

def segment_audio_with_continuous_repeats(audio_file, segment_duration=2, similarity_threshold=0.95):
    # Загружаем аудиофайл
    print(f"Загружается файл: {audio_file}")
    y, sr = librosa.load(audio_file, sr=None)
    segment_samples = int(sr * segment_duration)
    
    # Разделяем на сегменты
    segments = [y[i:i + segment_samples] for i in range(0, len(y), segment_samples)]
    print(f"Разделено на {len(segments)} сегментов по {segment_duration} секунде.")
    
    # Если последний сегмент короче, заполняем его нулями
    if len(segments[-1]) < segment_samples:
        segments[-1] = np.pad(segments[-1], (0, segment_samples - len(segments[-1])), 'constant')
    
    # Вычисляем пики для каждого сегмента
    peaks = [np.max(np.abs(segment)) for segment in segments]
    print("Вычислены пики для каждого сегмента.")
    
    # Сравниваем пики и проверяем последовательные повторения
    continuous_repeats = []  # Список для хранения информации о лупах
    current_repeat = []  # Текущая последовательность похожих сегментов

    for i in range(len(peaks) - 1):
        similarity = 1 - abs(peaks[i] - peaks[i + 1]) / max(peaks[i], peaks[i + 1])
        if similarity >= similarity_threshold:
            if not current_repeat:  # Если последовательность только начинается
                current_repeat = [i]
            current_repeat.append(i + 1)
        else:
            if len(current_repeat) > 4:  # Если текущая последовательность достаточно длинная, сохраняем её
                continuous_repeats.append(current_repeat)
            current_repeat = []  # Сбрасываем текущую последовательность
    
    # Добавляем последнюю последовательность, если она валидная
    if len(current_repeat) > 6:
        continuous_repeats.append(current_repeat)
    
    # Выводим информацию о найденных лупах
    if continuous_repeats:
        print("Найденные лупы:")
        for repeat_group in continuous_repeats:
            start_time = repeat_group[0] * segment_duration
            end_time = (repeat_group[-1] + 1) * segment_duration
            print(f"Луп с {start_time:.2f}с до {end_time:.2f}с (длина: {end_time - start_time:.2f}с)")
    else:
        print("Лупы не найдены.")
    
    # Построение графика аудио и сегментов
    plt.figure(figsize=(12, 6))
    times = np.arange(0, len(y)) / sr  # Время в секундах
    plt.plot(times, y, label="Аудиосигнал", color='b')
    
    # Отображаем сегменты, которые составляют лупы, с разными цветами
    for repeat_group in continuous_repeats:
        for idx in repeat_group:
            start_sample = idx * segment_samples
            end_sample = (idx + 1) * segment_samples
            color = generate_random_color()  # Генерируем случайный цвет для каждого сегмента
            plt.plot(np.linspace(start_sample / sr, end_sample / sr, len(segments[idx])), segments[idx], color=color, alpha=0.7)  # Отображаем сегменты лупа
    
    plt.title("Аудиосигнал с выделенными сегментами лупа")
    plt.xlabel("Время (сек.)")
    plt.ylabel("Амплитуда")
    plt.legend()
    plt.show()

    return continuous_repeats


# Пример использования
audio_file = 'audio_.mp3'  # Укажите путь к вашему файлу
continuous_repeats = segment_audio_with_continuous_repeats(audio_file)
