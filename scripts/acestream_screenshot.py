#!/usr/bin/env python3
import os
import sys
import time
import signal
import subprocess
import mss
import mss.tools

def cleanup_processes(processes):
    """Termina todos los procesos dados"""
    for p in processes:
        try:
            if p.poll() is None:  # Si el proceso sigue corriendo
                p.terminate()
                p.wait(timeout=5)
        except Exception as e:
            print(f"Error al terminar proceso: {e}")

def capture_acestream_screenshot(acestream_id, output_file='screenshot.png', wait_time=10):
    processes = []
    try:
        print(f'[1/5] Configurando entorno virtual de pantalla...')
        # Iniciar Xvfb como subproceso
        xvfb_process = subprocess.Popen(
            ['Xvfb', ':1', '-screen', '0', '1024x768x24'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(xvfb_process)
        os.environ['DISPLAY'] = ':1'
        time.sleep(2)

        print(f'[2/5] Iniciando stream de Acestream con ID: {acestream_id}')
        vlc_cmd = [
            'vlc',
            f'acestream://{acestream_id}',
            '--no-fullscreen',
            '--qt-start-minimized',
            '--vout', 'dummy',
            '--no-video-title-show',
            '--quiet'
        ]
        vlc_process = subprocess.Popen(
            vlc_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(vlc_process)
        
        print(f'[3/5] Esperando {wait_time} segundos...')
        time.sleep(wait_time)

        print('[4/5] Capturando pantalla...')
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            
            if screenshot.rgb is None or len(screenshot.rgb) == 0:
                raise ValueError("La captura de pantalla está vacía")
                
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_file)
            print(f'[5/5] Screenshot guardado como: {output_file}')
        
        return True
        
    except Exception as e:
        print(f'Error durante la captura: {str(e)}', file=sys.stderr)
        return False
    finally:
        print('Limpiando procesos...')
        cleanup_processes(processes)

if __name__ == "__main__":
    try:
        acestream_id = os.getenv('ACESTREAM_ID')
        if not acestream_id:
            raise ValueError("Se requiere el ID de Acestream")
            
        wait_time = int(os.getenv('WAIT_TIME', '10'))
        
        success = capture_acestream_screenshot(acestream_id, 'screenshot.png', wait_time)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error en la ejecución: {str(e)}", file=sys.stderr)
        sys.exit(1)
