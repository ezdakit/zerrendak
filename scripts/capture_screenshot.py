import os
import time
import subprocess

def capture_screenshot(acestream_id, output_folder):
    # Construye la URL de Ace Stream
    acestream_url = f"acestream://{acestream_id}"
    
    # Espera 10 segundos
    time.sleep(10)
    
    # Toma una captura de pantalla usando ffmpeg
    screenshot_command = f"ffmpeg -i http://127.0.0.1:6878/ace/getstream -vframes 1 {output_folder}/screenshot.png"
    os.system(screenshot_command)

if __name__ == "__main__":
    # Obtiene la ID de Ace Stream de las variables de entorno
    acestream_id = os.getenv('ACESTREAM_ID')
    
    # Define la carpeta de salida
    output_folder = "ace_kanalak"
    
    # Crea la carpeta de salida si no existe
    os.makedirs(output_folder, exist_ok=True)
    
    # Llama a la función para capturar la captura de pantalla
    capture_screenshot(acestream_id, output_folder)
