import os
import time
import subprocess

def capture_screenshot(acestream_id, output_folder):
    # Construye la URL de Ace Stream
    acestream_url = f"acestream://{acestream_id}"
    
    # Inicia el stream de Ace Stream
    stream_command = f"/usr/local/bin/acestream --client-console {acestream_url}"
    process = subprocess.Popen(stream_command, shell=True)
    
    # Espera 10 segundos
    time.sleep(10)
    
    # Toma una captura de pantalla usando ffmpeg
    screenshot_command = f"ffmpeg -i http://127.0.0.1:6878/ace/getstream -vframes 1 {output_folder}/screenshot.png"
    os.system(screenshot_command)
    
    # Termina el proceso de Ace Stream
    process.terminate()

if __name__ == "__main__":
    acestream_id = os.getenv('ACESTREAM_ID')  # Obtiene la ID de Ace Stream de las variables de entorno
    output_folder = "ace_kanalak"
    os.makedirs(output_folder, exist_ok=True)
    capture_screenshot(acestream_id, output_folder)
