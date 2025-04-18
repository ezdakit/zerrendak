from bs4 import BeautifulSoup
import csv
import re
from datetime import datetime
import argparse  # Añadir este import
import os
import sys

# Configurar el parser de argumentos
parser = argparse.ArgumentParser(description='Procesar eventos desde HTML a CSV y M3U')
parser.add_argument('--aux_folder', required=True, help='Directorio auxiliar para entrada HTML y salida CSV')
parser.add_argument('--listas_folder', required=True, help='Directorio para los archivos M3U de salida')
parser.add_argument('--html_file', help='Nombre del archivo HTML de entrada (sin ruta)')
parser.add_argument('--csv_file', help='Nombre del archivo CSV de salida (sin ruta)')
parser.add_argument('--m3u_events_file', help='Nombre del archivo M3U de eventos (sin ruta)')
parser.add_argument('--m3u_channels_file', help='Nombre del archivo M3U de canales (sin ruta)')

args = parser.parse_args()

# Establecer nombres por defecto si no se especifican
html_filename = args.html_file
csv_filename = args.csv_file
m3u_events_filename = args.m3u_events_file
m3u_channels_filename = args.m3u_channels_file

# Obtener la ruta del directorio padre del script
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)

# Construir rutas completas
aux_folder = os.path.join(parent_dir, args.aux_folder)
listas_folder = os.path.join(parent_dir, args.listas_folder)

# Crear directorios si no existen
os.makedirs(aux_folder, exist_ok=True)
os.makedirs(listas_folder, exist_ok=True)

# Rutas completas de archivos
html_file = os.path.join(aux_folder, html_filename)
csv_ekitaldiak_file_name = os.path.join(aux_folder, csv_filename)
m3u_ekitaldiak_file_name = os.path.join(listas_folder, m3u_events_filename)
m3u_kanalak_jatorrizko_file_name = os.path.join(aux_folder, m3u_channels_filename)

# Verificar que el archivo HTML existe
if not os.path.exists(html_file):
    print(f"Error: El archivo HTML {html_file} no existe")
    sys.exit(1)

def extract_and_save_kanalak_m3u(input_file, output_file):
    # Leer el contenido del archivo HTML
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Buscar el contenido de get.txt usando una expresión regular
    pattern = r"const fileContents = \{.*?'get\.txt': `(.*?)`.*?\}"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("No se encontró el contenido de get.txt en el archivo HTML")
        return
    
    m3u_content = match.group(1)

    # Reemplazar las secuencias de escape \n por saltos de línea reales
    m3u_content = m3u_content.replace('\\n', '\n')  # Convertir \n en saltos de línea reales
    m3u_content = m3u_content.replace('\\"', '"')   # Eliminar el escape de las comillas
    m3u_content = m3u_content.replace('\\\\', '\\') # Reemplazar \\ con \
    
    # Guardar el contenido en el archivo de salida
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(m3u_content)
    
    print(f"Archivo M3U guardado correctamente en {output_file}")

def format_match_info(match_cell):
    """Formatea correctamente la información del partido, manteniendo espacios entre elementos span"""
    match_info = match_cell.find('div', class_='match-info')
    if match_info:
        # Extraer texto preservando espacios entre elementos
        parts = []
        for element in match_info.find_all(['span', 'img']):
            if element.name == 'span':
                parts.append(element.get_text(strip=True))
            elif 'vs-text' in element.get('class', []):
                parts.append(' vs ')  # Mantener espacios alrededor del "vs"
        
        return ' '.join(parts).replace('  ', ' ').strip()
    else:
        # Si no hay match-info, usar el texto normal
        return match_cell.get_text(' ', strip=True)

def format_competition_info(competition_cell):
    """Formatea correctamente la información de la competición, combinando nombre y fase"""
    competition_info = competition_cell.find('div', class_='competition-info')
    if competition_info:
        name = competition_info.find('span', class_='competition-name')
        fase = competition_info.find('div', class_='fase')
        
        name_text = name.get_text(strip=True) if name else ''
        fase_text = fase.get_text(strip=True) if fase else ''
        
        # Combinar con un espacio si ambos existen
        if name_text and fase_text:
            return f"{name_text} {fase_text}"
        else:
            return name_text or fase_text
    else:
        return competition_cell.get_text(' ', strip=True)

def replace_commas_with_dots(data):
    """Reemplaza comas por puntos en todos los campos de un diccionario"""
    for key in data:
        if isinstance(data[key], str):
            data[key] = data[key].replace(",", ".")
    return data

with open(html_file, 'r', encoding='utf-8') as file:
    soup = BeautifulSoup(file.read(), 'html.parser')

# Ejecutar la extracción m3u
extract_and_save_kanalak_m3u(html_file, m3u_kanalak_jatorrizko_file_name)

csv_data = []

# Buscar el contenedor de eventos
events_container = soup.find('div', id='eventsContainer')
if not events_container:
    print("No se encontró el contenedor de eventos (div#eventsContainer)")
    exit()

# Procesar cada día de eventos
for day in events_container.find_all('div', class_='events-day'):
    # Extraer fecha del atributo data-date o del texto h2
    date_from_attr = day.get('data-date', '')
    date_from_text = re.search(r'(\d{2}/\d{2}/\d{4})', day.h2.get_text() if day.h2 else '')
    
    date = date_from_attr if date_from_attr else (date_from_text.group(1) if date_from_text else 'Fecha desconocida')
    
    # Buscar todas las filas de evento principal (event-row)
    for event_row in day.find_all('tr', class_='event-row'):
        event_id = event_row.get('data-event-id', '')
        
        # Buscar la fila de detalles correspondiente (mismo data-event-id)
        detail_row = day.find('tr', class_='event-detail', attrs={'data-event-id': event_id})
        if not detail_row:
            continue  # Si no hay fila de detalles, saltar este evento
        
        # Extraer información básica del evento
        cols = event_row.find_all('td')
        if len(cols) < 4:
            continue
        
        time = cols[0].get_text(strip=True)
        competition = format_competition_info(cols[1])  # Usamos la nueva función de formateo
        match = format_match_info(cols[2])
        
        # Crear un event_id más descriptivo si el actual es genérico
        if event_id.endswith('--'):
            teams = match.split(' vs ') if ' vs ' in match else [match]
            event_id = f"{time}-{'-'.join([t.strip() for t in teams])}"
        
        # Procesar los grupos de streams
        for group in detail_row.find_all('div', class_='stream-channel-group'):
            group_name = group.find('h4').get_text(strip=True) if group.find('h4') else 'Sin grupo'
            
            # Buscar todos los enlaces de Acestream en este grupo
            for link in group.find_all('a', class_='stream-link', 
                                     onclick=re.compile(r"openAcestream\('([a-f0-9]+)'")):
                acestream_id = re.search(r"openAcestream\('([a-f0-9]+)'", link['onclick']).group(1)
                
                # Determinar calidad (FHD, SD, etc.)
                quality = 'FHD' if 'FHD' in link.get_text() else ('SD' if 'SD' in link.get_text() else '')
                
                # Crear el diccionario y reemplazar comas por puntos
                entry = {
                    'date': date,
                    'event_id': event_id,
                    'time': time,
                    'competition': competition,
                    'match': match,
                    'group': group_name,
                    'acestream_id': acestream_id,
                    'quality': quality
                }
                csv_data.append(replace_commas_with_dots(entry))

# Escribir el archivo CSV
if csv_data:
    with open(csv_ekitaldiak_file_name, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['date', 'event_id', 'time', 'competition', 'match', 'group', 'acestream_id', 'quality']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(csv_data)
    print(f"Archivo CSV creado exitosamente con {len(csv_data)} entradas de Acestream.")
else:
    print("No se encontraron eventos con IDs de Acestream.")



# Write the header lines
header_lines = [
    '#EXTM3U url-tvg="https://raw.githubusercontent.com/davidmuma/EPG_dobleM/refs/heads/master/guiatv.xml"\n',
    '#EXTVLCOPT:network-caching=2000\n',
    '\n'
]

with open(m3u_ekitaldiak_file_name, 'w', encoding='utf-8') as out_file:
    # Write header
    out_file.writelines(header_lines)
    
    # Read CSV and write entries
    with open(csv_ekitaldiak_file_name, 'r', encoding='utf-8') as in_file:
        reader = csv.DictReader(in_file)
        
        for row in reader:
            # Format date from YYYY-MM-DD to DD-MM
            date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
            date_formated = date_obj.strftime('%d/%m')
            
            # Get quality if available, otherwise empty string
            quality = row['quality'] if row['quality'] else ''
            
            # Create EXTINF line
            extinf_line = f'#EXTINF:-1 tvg-id="" group-title="{date_formated} {row["competition"]}", {row["time"]} {row["match"]} {row["group"]} {quality}\n'
            
            # Create URL line
            url_line = f'http://127.0.0.1:6878/ace/getstream?id={row["acestream_id"]}\n'
            
            # Write both lines to output file
            out_file.write(extinf_line)
            out_file.write(url_line)

print(f"M3U file generated successfully at {m3u_ekitaldiak_file_name}")
