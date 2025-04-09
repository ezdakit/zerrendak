import os
import time
import subprocess

def capture_screenshot(acestream_url, output_folder):
    # Inicia el stream de acestream
    stream_command = f"acestreamengine --client-console {acestream_url}"
    process = subprocess.Popen(stream_command, shell=True)
    
    # Espera 10 segundos
    time.sleep(10)
    
    # Toma una captura de pantalla usando ffmpeg
    screenshot_command = f"ffmpeg -i http://127.0.0.1:6878/ace/getstream -vframes 1 {output_folder}/screenshot.png"
    os.system(screenshot_command)
    
    # Termina el proceso de acestream
    process.terminate()

if __name__ == "__main__":
    acestream_url = "acestream://your_acestream_url"
    output_folder = "ace_kanalak"
    os.makedirs(output_folder, exist_ok=True)
    capture_screenshot(acestream_url, output_folder)
