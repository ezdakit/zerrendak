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
                os.kill(p.pid, signal.SIGTERM)
                p.wait(timeout=5)
        except Exception as e:
            print(f"Error al terminar proceso: {e}", file=sys.stderr)

def capture_screenshot(output_file='screenshot.png', wait_time=10):
    """Captura un screenshot después de esperar"""
    try:
        print(f'[1/3] Esperando {wait_time} segundos...')
        time.sleep(wait_time)
        
        print('[2/3] Capturando pantalla...')
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            
            if not screenshot or not screenshot.rgb:
                raise ValueError("La captura de pantalla está vacía")
                
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_file)
            print(f'[3/3] Screenshot guardado como: {output_file}')
        
        return True
        
    except Exception as e:
        print(f'Error durante la captura: {str(e)}', file=sys.stderr)
        return False

if __name__ == "__main__":
    try:
        wait_time = int(os.getenv('WAIT_TIME', '20'))
        success = capture_screenshot('screenshot.png', wait_time)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error en la ejecución: {str(e)}", file=sys.stderr)
        sys.exit(1)
