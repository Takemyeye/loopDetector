import numpy as np
import pyaudio
import time
from scipy.signal.windows import hann

# Параметры
segment_length = 4 * 44100  # 4 секунды (увеличили длительность фрагмента)
loop_threshold = 0.3  # Порог схожести (понизили порог до 0.3 для большей чувствительности)
min_loop_duration = 10  # Минимальная длительность лупа в секундах
max_segments_in_memory = 30  # Количество сегментов, хранимых в памяти

# Переменные для хранения состояния
segments = []  # История последних сегментов
loop_start_time = None  # Время начала лупа
loop_found = False  # Статус нахождения лупа
current_time = 0  # Текущее время в секундах

# Функция для вычисления схожести между двумя фрагментами
def similarity_check(segment1, segment2):
    # Применяем окно Ханнинга для снижения шума
    segment1 = segment1 * hann(len(segment1))
    segment2 = segment2 * hann(len(segment2))
    
    # Используем корреляцию Пирсона
    return np.corrcoef(segment1, segment2)[0, 1]

# Функция для прослушивания потока аудио и анализа лупа
def process_audio_stream():
    global loop_found, loop_start_time, segments, current_time  # Добавляем глобальные переменные

    # Инициализация pyaudio
    p = pyaudio.PyAudio()

    # Открываем поток с аудио
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=segment_length)

    print("Начинается анализ потока аудио...")

    # Ожидаем 20 секунд перед началом анализа, чтобы собрать достаточно данных
    print("Ожидаем 20 секунд для накопления сегментов...")
    time.sleep(20)

    # Основной цикл обработки потока аудио
    while True:
        # Чтение данных с потока
        audio_data = stream.read(segment_length)
        
        # Преобразуем данные в numpy массив и нормализуем
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        # Добавляем текущий сегмент в память
        segments.append(audio_np)
        if len(segments) > max_segments_in_memory:  # Ограничиваем количество сегментов в памяти
            segments.pop(0)

        # Если нет достаточного количества сегментов для анализа, пропускаем итерацию
        if len(segments) < 2:
            current_time += 1  # Увеличиваем время на 1 секунду
            continue

        # Проверяем схожесть с предыдущими сегментами (ограничиваем число проверок)
        for i in range(len(segments) - 1):
            similarity = similarity_check(audio_np, segments[i])

            # Логирование схожести
            print(f"Схожесть между сегментами на {current_time} секунд: {similarity:.2f}")

            if similarity > loop_threshold:
                # Луп найден
                if not loop_found:
                    loop_start_time = time.time()
                    loop_found = True
                    print(f"Луп найден на {current_time} секунд!")

                # Прерываем, если длительность лупа превышает порог
                loop_duration = time.time() - loop_start_time
                if loop_duration >= min_loop_duration:
                    print(f"Луп продолжается: {loop_duration:.2f} секунд")
                    break
                break
        else:
            # Если не найдено схожести, сбрасываем флаг лупа
            if loop_found:
                loop_found = False
                print(f"Луп закончился через {time.time() - loop_start_time:.2f} секунд на {current_time} секунд")
                loop_start_time = None

        # Увеличиваем текущее время на 1 секунду
        current_time += 1

    # Завершаем поток
    stream.stop_stream()
    stream.close()
    p.terminate()

# Запуск анализа потока
process_audio_stream()
