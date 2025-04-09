#!/usr/bin/env python3
import os
import time
import requests
import logging

def check_acestream_health(port=6878, timeout=30):
    """Verifica si el servidor Acestream está listo"""
    start_time = time.time()
    health_url = f"http://localhost:{port}/webui/api/service/version"
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                logging.info("Acestream está listo")
                return True
        except requests.exceptions.RequestException:
            pass
        
        logging.info("Esperando a que Acestream inicie...")
        time.sleep(5)
    
    logging.error("Timeout: Acestream no se inició correctamente")
    return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if not check_acestream_health():
        sys.exit(1)
