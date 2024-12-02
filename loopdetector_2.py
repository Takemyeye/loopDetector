import requests
import librosa
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import io
import time

# Функция для вычисления автокорреляции
def autocorrelation(x):
    result = np.correlate(x, x, mode='full')
    return result[result.size // 2:]

# Функция для обработки аудио потока
def process_audio_stream(url, segment_duration=10):
    try:
        print("Попытка подключения к потоку...")
        audio_stream = requests.get(url, stream=True)
        print("Подключение установлено")

        audio_data = b""
        chunk_size = 2048  # Увеличили размер чанка
        sample_rate = 22050

        while True:
            chunk = audio_stream.iter_content(chunk_size=chunk_size)
            audio_data += next(chunk)

            try:
                y, sr = librosa.load(io.BytesIO(audio_data), sr=sample_rate)
                print(f"Загружено {len(y)} сэмплов для анализа.")

                # Нормализация аудио сигнала
                y = librosa.util.normalize(y)

                segment_samples = segment_duration * sr
                for i in range(0, len(y), segment_samples):
                    segment = y[i:i + segment_samples]

                    if len(segment) < segment_samples:
                        break

                    print(f"Проверка лупа на сегменте с {i / sr} секунд")
                    auto_corr = autocorrelation(segment)

                    # Поиск пиков в автокорреляции с улучшенными параметрами
                    peaks, _ = signal.find_peaks(auto_corr, height=0.1, distance=1000)
                    if len(peaks) > 1:
                        print(f"Луп найден на {i / sr} секунд.")
                    else:
                        print(f"Лупа нет на {i / sr} секунд.")

                    time.sleep(10)

            except Exception as e:
                print(f"Ошибка при обработке потока: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения к потоку: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

# Пример использования
url = "http://audio1.meway.tv:8099/live"
process_audio_stream(url)
