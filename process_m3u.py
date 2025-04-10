import os
import re
import requests
import hashlib
from urllib.parse import urlparse
import cv2
import subprocess
import time

# Configuración
M3U_FILE = "aux/kanalak_jatorrizko.m3u"
LOGOS_DIR = "logos_canales"
SCREENSHOTS_DIR = "canales_screenshots"
TIMEOUT_SECONDS = 15
ACESTREAM_PORT = 6878

def ensure_dir(directory):
    os.makedirs(directory, exist_ok=True)

def clean_dir(directory):
    if os.path.exists(directory):
        for f in os.listdir(directory):
            os.remove(os.path.join(directory, f))
    else:
        os.makedirs(directory)

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def download_logo(url, tvg_id):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        ext = os.path.splitext(urlparse(url).path)[1] or ".png"
        base_filename = f"{safe_filename(tvg_id)}{ext}"
        filename = os.path.join(LOGOS_DIR, base_filename)
        
        # Verificar si existe y es diferente
        counter = 1
        while os.path.exists(filename):
            with open(filename, 'rb') as f:
                existing_hash = hashlib.md5(f.read()).hexdigest()
            new_hash = hashlib.md5(response.content).hexdigest()
            
            if existing_hash == new_hash:
                return filename
            
            filename = os.path.join(LOGOS_DIR, 
                                  f"{safe_filename(tvg_id)}-{counter}{ext}")
            counter += 1
        
        with open(filename, 'wb') as f:
            f.write(response.content)
            
        return filename
    except Exception as e:
        print(f"❌ Error descargando logo {url}: {str(e)}")
        return None

def capture_stream_screenshot(stream_url, output_path):
    try:
        # Usamos ffmpeg para capturar el frame
        command = [
            'ffmpeg',
            '-y',
            '-ss', '10',
            '-i', stream_url,
            '-frames:v', '1',
            '-f', 'image2',
            '-loglevel', 'error',
            output_path
        ]
        subprocess.run(command, check=True, timeout=TIMEOUT_SECONDS)
        return True
    except subprocess.TimeoutExpired:
        print(f"⌛ Timeout al capturar {stream_url}")
    except Exception as e:
        print(f"❌ Error capturando {stream_url}: {str(e)}")
    return False

def process_m3u_file():
    ensure_dir(LOGOS_DIR)
    clean_dir(SCREENSHOTS_DIR)
    
    with open(M3U_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Expresión regular para extraer información
    pattern = re.compile(
        r'#EXTINF:-1.*?tvg-logo="(?P<logo_url>[^"]+)".*?tvg-id="(?P<tvg_id>[^"]+)".*?group-title="[^"]*",(?P<channel_name>[^\n]+)\n(?P<stream_url>http[^\n]+)',
        re.DOTALL
    )
    
    for match in pattern.finditer(content):
        logo_url = match.group('logo_url')
        tvg_id = match.group('tvg_id')
        channel_name = match.group('channel_name').strip()
        stream_url = match.group('stream_url')
        stream_id = stream_url.split('=')[-1]
        
        print(f"\n📺 Procesando: {channel_name}")
        
        # Paso 1: Descargar logo
        print(f"🖼️ Descargando logo...")
        logo_path = download_logo(logo_url, tvg_id)
        if logo_path:
            print(f"✅ Logo guardado: {os.path.basename(logo_path)}")
        
        # Paso 2: Capturar screenshot del stream
        screenshot_filename = f"{safe_filename(channel_name)} - {stream_id}.jpg"
        screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
        
        print(f"🎥 Capturando stream ({TIMEOUT_SECONDS}s)...")
        if capture_stream_screenshot(stream_url, screenshot_path):
            print(f"📸 Screenshot guardado: {screenshot_filename}")
            
            # Verificar calidad de la captura
            try:
                img = cv2.imread(screenshot_path)
                if img is None or img.size == 0:
                    print("⚠️ Captura vacía o corrupta")
                    os.remove(screenshot_path)
                else:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    fm = cv2.Laplacian(gray, cv2.CV_64F).var()
                    print(f"📊 Calidad de imagen: {fm:.2f}")
            except Exception as e:
                print(f"⚠️ Error analizando imagen: {str(e)}")
        else:
            print("❌ Fallo en la captura")

if __name__ == "__main__":
    print("🚀 Iniciando procesamiento del archivo M3U")
    start_time = time.time()
    
    process_m3u_file()
    
    elapsed = time.time() - start_time
    print(f"\n✅ Proceso completado en {elapsed:.2f} segundos")
    print(f"📂 Logos guardados en: {LOGOS_DIR}")
    print(f"📂 Screenshots guardados en: {SCREENSHOTS_DIR}")
