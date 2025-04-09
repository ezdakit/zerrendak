import os
import time
import subprocess

def capture_screenshot(output_folder):
    # URL de Ace Stream con la ID proporcionada
    acestream_url = "acestream://1205151f6fa5d95c0eeb543cbce43ccfa6a1b216"
    
    # Inicia el stream de Ace Stream en el contenedor
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
    # Define la carpeta de salida
    output_folder = "ace_kanalak"
    
    # Crea la carpeta de salida si no existe
    os.makedirs(output_folder, exist_ok=True)
    
    # Llama a la función para capturar la captura de pantalla
    capture_screenshot(output_folder)
