import os
import requests

def scarica_segmento_audio(url, output_file, segment_size=360000):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check if the request was successful
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
                # If the file size exceeds the limit, stop downloading
                if os.path.getsize(output_file) >= segment_size:
                    break
        return True
    except Exception as e:
        print(f"Error downloading audio from {url}: {e}")
        return False

def mantieni_limite_file(directory, limite=4):
    try:
        files = sorted(
            [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))],
            key=lambda x: os.path.getctime(os.path.join(directory, x))
        )
        while len(files) > limite:
            file_to_delete = files.pop(0)
            os.remove(os.path.join(directory, file_to_delete))
            print(f"Deleted file: {file_to_delete}")
    except Exception as e:
        print(f"Error managing files in directory: {e}")
