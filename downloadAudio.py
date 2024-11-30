import requests
import time

url = "http://audio1.meway.tv:8099/live"
file_path = "downloaded_audio_30s.mp3"

response = requests.get(url, stream=True)

if response.status_code == 200:
    with open(file_path, "wb") as f:
        start_time = time.time()
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                elapsed_time = time.time() - start_time
                if elapsed_time >= 30:
                    break
        
        print(f"Загружено {elapsed_time:.2f} секунд.")
        print(f"Аудиофайл был успешно сохранен как {file_path}")
else:
    print(f"Ошибка при подключении: {response.status_code}")
