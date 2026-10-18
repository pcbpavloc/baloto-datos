"""
Script para actualizar baloto_era_actual.csv
Descarga los últimos sorteos de baloto.com y los agrega si son nuevos.
"""
import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

# URL de la fuente oficial
URL = "https://baloto.com/resultados"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# Ruta del CSV (ajusta si está dentro de una carpeta, ej: "datos/baloto_era_actual.csv")
CSV_PATH = "baloto_era_actual.csv"

def normalizar_fecha(fecha_texto):
    """Convierte '14 de Octubre de 2026' a '2026-10-14' para que coincida con el CSV"""
    meses = {
        'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
        'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
        'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
    }
    try:
        partes = fecha_texto.split(' de ')
        if len(partes) == 3:
            dia = partes[0].strip().zfill(2)
            mes = meses.get(partes[1].strip(), '01')
            anio = partes[2].strip()
            return f"{anio}-{mes}-{dia}"
    except Exception:
        pass
    return fecha_texto # Fallback por si el formato de la web cambia

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
                    
                    fecha = normalizar_fecha(fecha_texto)
                    
                    sorteos.append({
                        'fecha': fecha,
                        'n1': n1, 'n2': n2, 'n3': n3,
                        'n4': n4, 'n5': n5,
                        'superbalota': superbalota
                    })
        
        # La web devuelve del más reciente al más antiguo. 
        # Invertimos para agregar al CSV en orden cronológico (del antiguo al nuevo)
        sorteos.reverse()
        return sorteos
    except Exception as e:
        print(f"❌ Error al descargar: {e}")
        return []

def cargar_sorteos_existentes():
    fechas_existentes = set()
    if os.path.exists(CSV_PATH):
        # Abrir con encoding utf-8-sig para manejar BOM
        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            lector = csv.DictReader(f, delimiter=';')
            
            # Debug: mostrar los nombres de columna que encuentra
            print(f"📋 Columnas encontradas: {lector.fieldnames}")
            
            for i, fila in enumerate(lector):
                # Debug: mostrar la primera fila
                if i == 0:
                    print(f" Primera fila: {fila}")
                
                # Intentar con diferentes nombres posibles
                fecha = fila.get('fecha', fila.get(' fecha', ''))
                if fecha:
                    fechas_existentes.add(fecha.strip())
    return fechas_existentes

def agregar_nuevos_sorteos(sorteos_nuevos):
    """Agrega los sorteos nuevos al final del CSV"""
    if not sorteos_nuevos:
        print("ℹ️ No hay sorteos nuevos para agregar.")
        return
    
    archivo_existe = os.path.exists(CSV_PATH)
    
    with open(CSV_PATH, 'a', encoding='utf-8-sig', newline='') as f:
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
    
    print(f"✅ {len(sorteos_nuevos)} sorteos nuevos agregados correctamente.")

def main():
    print(f"🔄 Actualizando Baloto - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. Cargar fechas existentes
    fechas_existentes = cargar_sorteos_existentes()
    print(f"📊 Sorteos existentes en CSV: {len(fechas_existentes)}")
    
    # 2. Obtener nuevos sorteos de la web
    sorteos_web = obtener_ultimos_sorteos()
    print(f"🌐 Sorteos descargados de la web: {len(sorteos_web)}")
    
    # 3. Filtrar solo los que no estén en el CSV
    nuevos = [s for s in sorteos_web if s['fecha'] not in fechas_existentes]
    print(f"🆕 Sorteos realmente nuevos: {len(nuevos)}")
    
    # 4. Agregar al CSV
    agregar_nuevos_sorteos(nuevos)
    
    print("✅ Proceso de actualización finalizado.")

if __name__ == "__main__":
    main()
