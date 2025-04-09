import os
import time
import subprocess

def capture_screenshot(acestream_id, output_folder):
    # Construye la URL de Ace Stream
    acestream_url = f"acestream://{acestream_id}"
    
    # Inicia el stream de Ace Stream
    stream_command = f"docker exec acestream acestreamengine --client-console {acestream_url}"
    process = subprocess.Popen(stream_command, shell=True)
    
    # Espera 10 segundos
    time.sleep(10)
    
    # Toma una captura de pantalla usando ffmpeg
    screenshot_command = f"ffmpeg -i http://127.0.0.1:6878/ace/getstream -vframes 1 {output_folder}/screenshot.png"
    os.system(screenshot_command)
    
    # Termina el proceso de Ace Stream
    process.terminate()

if __name__ == "__main__":
    # ID de Ace Stream hardcoded
    acestream_id = "1205151f6fa5d95c0eeb543cbce43ccfa6a1b216"
    
    # Define la carpeta de salida
    output_folder = "ace_kanalak"
    
    # Crea la carpeta de salida si no existe
    os.makedirs(output_folder, exist_ok=True)
    
    # Llama a la función para capturar la captura de pantalla
    capture_screenshot(acestream_id, output_folder)
