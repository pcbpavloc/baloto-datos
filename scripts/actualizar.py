"""
Script para actualizar baloto_era_actual.csv
Descarga los últimos sorteos de baloto.com
"""
import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

# URL de la fuente oficial
URL = "https://baloto.com/resultados"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Ruta del CSV (ajusta según tu estructura)
CSV_PATH = "baloto_era_actual.csv"

def obtener_ultimos_sorteos():
    """Descarga los sorteos más recientes de baloto.com"""
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tabla = soup.find('table')
        if not tabla:
            print("❌ No se encontró tabla en la página")
            return []
        
        sorteos = []
        filas = tabla.find_all('tr')[1:]  # Saltar encabezado
        
        for fila in filas:
            celdas = fila.find_all('td')
            if len(celdas) >= 3:
                fecha_texto = celdas[1].text.strip()
                numeros_texto = celdas[2].text.strip()
                
                # Parsear números (formato: "05 - 06 - 07 - 19 - 40 - 03")
                partes = [n.strip() for n in numeros_texto.split('-')]
                if len(partes) == 6:
                    n1, n2, n3, n4, n5 = partes[:5]
                    superbalota = partes[5]
                    
                    # Normalizar fecha
                    fecha = fecha_texto.replace(' de ', '-')
                    
                    sorteos.append({
                        'fecha': fecha,
                        'n1': n1, 'n2': n2, 'n3': n3,
                        'n4': n4, 'n5': n5,
                        'superbalota': superbalota
                    })
        
        return sorteos
    except Exception as e:
        print(f"❌ Error al descargar: {e}")
        return []

def cargar_sorteos_existentes():
    fechas_existentes = set()
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            lector = csv.DictReader(f, delimiter=';')  # ✅ Agregado delimiter
            for fila in lector:
                fechas_existentes.add(fila['fecha'])
    return fechas_existentes

def agregar_nuevos_sorteos(sorteos_nuevos):
    """Agrega los sorteos nuevos al final del CSV"""
    if not sorteos_nuevos:
        print("ℹ️ No hay sorteos nuevos")
        return
    
    archivo_existe = os.path.exists(CSV_PATH)
    
    with open(CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        campos = ['fecha', 'sorteo', 'era', 'formato', 
                  'n1', 'n2', 'n3', 'n4', 'n5', 'n6',
                  'superbalota', 'rev1', 'rev2', 'rev3', 
                  'rev4', 'rev5', 'rev6', 'rev_super',
                  'revancha', 'fuente']
        
        escritor = csv.DictWriter(f, fieldnames=campos, delimiter=';')
        
        if not archivo_existe:
            escritor.writeheader()
        
        for s in sorteos_nuevos:
            fila = {
                'fecha': s['fecha'],
                'sorteo': '',
                'era': 'actual',
                'formato': '5/43 + super 1/16',
                'n1': s['n1'], 'n2': s['n2'], 'n3': s['n3'],
                'n4': s['n4'], 'n5': s['n5'], 'n6': '',
                'superbalota': s['superbalota'],
                'rev1': '', 'rev2': '', 'rev3': '',
                'rev4': '', 'rev5': '', 'rev6': '',
                'rev_super': '', 'revancha': '',
                'fuente': 'W · baloto.com'
            }
            escritor.writerow(fila)
    
    print(f"✅ {len(sorteos_nuevos)} sorteos nuevos agregados")

def main():
    print(f"🔄 Actualizando Baloto - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. Cargar fechas existentes
    fechas_existentes = cargar_sorteos_existentes()
    print(f"📊 Sorteos existentes: {len(fechas_existentes)}")
    
    # 2. Obtener nuevos sorteos
    sorteos = obtener_ultimos_sorteos()
    print(f" Sorteos descargados: {len(sorteos)}")
    
    # 3. Filtrar solo los nuevos
    nuevos = [s for s in sorteos if s['fecha'] not in fechas_existentes]
    print(f"🆕 Sorteos nuevos: {len(nuevos)}")
    
    # 4. Agregar al CSV
    agregar_nuevos_sorteos(nuevos)

if __name__ == "__main__":
    main()
