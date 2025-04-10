#!/usr/bin/env python3
import os
import re
import requests
import hashlib
from urllib.parse import urlparse
import cv2
import subprocess
import time
import argparse
from math import ceil
import sys

# Configuración
M3U_FILE = "aux/kanalak_jatorrizko.m3u"
LOGOS_DIR = "logos_canales"
SCREENSHOTS_DIR = "canales_screenshots"
TIMEOUT_SECONDS = 25
ACESTREAM_PORT = 6878
MAX_RETRIES = 3
RETRY_DELAY = 10

def parse_arguments():
    parser = argparse.ArgumentParser(description='Procesar archivo M3U y capturar streams')
    parser.add_argument('--chunk', type=int, default=1, help='Número del chunk actual (1-based)')
    parser.add_argument('--total-chunks', type=int, default=1, help='Total de chunks paralelos')
    return parser.parse_args()

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

def download_with_retry(url, max_retries=MAX_RETRIES):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(RETRY_DELAY * (attempt + 1))

def download_logo(logo_url, tvg_id):
    try:
        response = download_with_retry(logo_url)
        ext = os.path.splitext(urlparse(logo_url).path)[1] or ".png"
        base_filename = f"{safe_filename(tvg_id)}{ext}"
        filename = os.path.join(LOGOS_DIR, base_filename)
        
        # Verificar duplicados
        counter = 1
        while os.path.exists(filename):
            with open(filename, 'rb') as f:
                existing_hash = hashlib.md5(f.read()).hexdigist()
            new_hash = hashlib.md5(response.content).hexdigest()
            
            if existing_hash == new_hash:
                return filename  # Archivo idéntico
            
            filename = os.path.join(LOGOS_DIR, 
                                  f"{safe_filename(tvg_id)}-{counter}{ext}")
            counter += 1
        
        with open(filename, 'wb') as f:
            f.write(response.content)
            
        return filename
    except Exception as e:
        print(f"❌ Error descargando logo {logo_url}: {str(e)}")
        return None

def capture_stream(stream_url, output_path, timeout=TIMEOUT_SECONDS):
    command = [
        'ffmpeg',
        '-y',
        '-ss', '10',  # Esperar 10 segundos
        '-i', stream_url,
        '-frames:v', '1',
        '-f', 'image2',
        '-loglevel', 'error',
        output_path
    ]
    
    for attempt in range(MAX_RETRIES):
        try:
            subprocess.run(command, check=True, timeout=timeout)
            
            # Verificar que la imagen no está corrupta
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise ValueError("Captura vacía")
                
            img = cv2.imread(output_path)
            if img is None:
                raise ValueError("Imagen no válida")
                
            return True
        except subprocess.TimeoutExpired:
            print(f"⌛ Timeout (intento {attempt + 1}/{MAX_RETRIES})")
            if attempt == MAX_RETRIES - 1:
                return False
        except Exception as e:
            print(f"⚠️ Error en intento {attempt + 1}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                return False
        time.sleep(RETRY_DELAY * (attempt + 1))

def analyze_image_quality(image_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            return 0.0
        
        # Convertir a escala de grises y calcular nitidez
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Verificar si es una pantalla negra
        if fm < 1.0 and gray.mean() < 10:
            return -1.0  # Indicador de pantalla negra
            
        return fm
    except Exception as e:
        print(f"⚠️ Error analizando imagen: {str(e)}")
        return 0.0

def process_m3u_file(chunk, total_chunks):
    ensure_dir(LOGOS_DIR)
    clean_dir(SCREENSHOTS_DIR)
    
    with open(M3U_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Expresión regular optimizada
    pattern = re.compile(
        r'#EXTINF:-1.*?tvg-logo="(?P<logo_url>[^"]+)".*?tvg-id="(?P<tvg_id>[^"]+)".*?group-title="[^"]*",(?P<channel_name>[^\n]+)\n(?P<stream_url>http[^\n]+)',
        re.DOTALL
    )
    
    all_matches = list(pattern.finditer(content))
    total_items = len(all_matches)
    chunk_size = ceil(total_items / total_chunks)
    start_idx = (chunk - 1) * chunk_size
    end_idx = min(start_idx + chunk_size, total_items)
    matches = all_matches[start_idx:end_idx]
    
    print(f"📊 Procesando chunk {chunk}/{total_chunks} ({len(matches)} canales)")
    
    results = []
    for idx, match in enumerate(matches, 1):
        logo_url = match.group('logo_url')
        tvg_id = match.group('tvg_id')
        channel_name = match.group('channel_name').strip()
        stream_url = match.group('stream_url')
        stream_id = stream_url.split('=')[-1]
        
        print(f"\n📺 [{idx}/{len(matches)}] Procesando: {channel_name[:50]}...")
        
        # Descargar logo
        logo_path = download_logo(logo_url, tvg_id)
        logo_status = bool(logo_path)
        
        # Capturar screenshot
        screenshot_filename = f"{safe_filename(channel_name)} - {stream_id}.jpg"
        screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
        
        capture_success = capture_stream(stream_url, screenshot_path)
        quality_score = analyze_image_quality(screenshot_path) if capture_success else 0.0
        
        if quality_score == -1.0:
            print("🖥️  ¡Pantalla negra detectada! Eliminando...")
            os.remove(screenshot_path)
            capture_success = False
        
        results.append({
            'channel': channel_name,
            'stream_id': stream_id,
            'logo_downloaded': logo_status,
            'capture_success': capture_success,
            'quality_score': quality_score
        })
        
        # Reporte intermedio
        if capture_success:
            print(f"📸 Captura exitosa (Calidad: {quality_score:.2f})")
        else:
            print("❌ Fallo en la captura")
    
    return results

def generate_report(results, chunk, total_chunks):
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'chunk': f"{chunk}/{total_chunks}",
        'total_channels': len(results),
        'successful_captures': sum(1 for r in results if r['capture_success']),
        'average_quality': sum(r['quality_score'] for r in results if r['capture_success']) / max(1, sum(1 for r in results if r['capture_success'])),
        'details': results
    }
    
    report_filename = f"report_chunk_{chunk}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_filename

if __name__ == "__main__":
    args = parse_arguments()
    start_time = time.time()
    
    print(f"🚀 Iniciando procesamiento (Chunk {args.chunk}/{args.total_chunks})")
    
    try:
        results = process_m3u_file(args.chunk, args.total_chunks)
        report_file = generate_report(results, args.chunk, args.total_chunks)
        
        elapsed = time.time() - start_time
        success_rate = (sum(1 for r in results if r['capture_success']) / len(results)) * 100
        
        print(f"\n✅ Proceso completado en {elapsed:.2f} segundos")
        print(f"📊 Estadísticas:")
        print(f"   - Canales procesados: {len(results)}")
        print(f"   - Capturas exitosas: {success_rate:.1f}%")
        print(f"   - Calidad promedio: {sum(r['quality_score'] for r in results if r['capture_success']) / max(1, sum(1 for r in results if r['capture_success'])):.2f}")
        print(f"📄 Reporte guardado en: {report_file}")
        
        # Salida con código de estado (útil para GitHub Actions)
        if success_rate < 50.0:
            print("⚠️ Advertencia: Menos del 50% de capturas exitosas")
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")
        sys.exit(1)
