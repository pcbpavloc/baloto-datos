"""
Script para actualizar baloto_era_actual.csv
Descarga los últimos sorteos de Baloto y Revancha de baloto.com
"""
import requests
from bs4 import BeautifulSoup
import csv
import os
import re
from datetime import datetime

# URL de la fuente oficial
URL = "https://baloto.com/resultados"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# Ruta del CSV
CSV_PATH = "baloto_era_actual.csv"

def normalizar_fecha(fecha_texto):
    """Convierte '17 de Octubre de 2026' a '2026-10-17'"""
    meses = {
        'Enero': '01', 'Febrero': '02', 'Marzo': '03', 'Abril': '04',
        'Mayo': '05', 'Junio': '06', 'Julio': '07', 'Agosto': '08',
        'Septiembre': '09', 'Octubre': '10', 'Noviembre': '11', 'Diciembre': '12'
    }
    try:
        # Buscar patrón: "17 de Octubre de 2026"
        match = re.search(r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', fecha_texto)
        if match:
            dia = match.group(1).zfill(2)
            mes = meses.get(match.group(2), '01')
            anio = match.group(3)
            return f"{anio}-{mes}-{dia}"
    except Exception:
        pass
    return fecha_texto

def extraer_numeros(texto):
    """Extrae números de un texto como '06 - 09 - 12 - 26 - 29 - 09'"""
    # Buscar todos los números en el texto
    numeros = re.findall(r'\d+', texto)
    return [n.zfill(2) for n in numeros]

def identificar_tipo_sorteo(celda_sorteo):
    """Identifica si es Baloto o Revancha buscando el texto/logo"""
    texto = celda_sorteo.get_text().lower()
    if 'revancha' in texto or 'revancha!' in texto:
        return 'revancha'
    elif 'baloto' in texto:
        return 'baloto'
    return None

def obtener_sorteos():
    """Descarga Baloto y Revancha de la página oficial"""
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tabla = soup.find('table')
        if not tabla:
            print("❌ No se encontró tabla en la página")
            return []
        
        # Diccionario para agrupar por fecha
        sorteos_por_fecha = {}
        
        filas = tabla.find_all('tr')[1:]  # Saltar encabezado
        
        for fila in filas:
            celdas = fila.find_all('td')
            if len(celdas) >= 3:
                # Columna 1: Tipo de sorteo (Baloto o Revancha)
                tipo = identificar_tipo_sorteo(celdas[0])
                
                # Columna 2: Fecha
                fecha_texto = celdas[1].text.strip()
                fecha = normalizar_fecha(fecha_texto)
                
                # Columna 3: Números
                numeros_texto = celdas[2].text.strip()
                numeros = extraer_numeros(numeros_texto)
                
                # Debe tener 6 números (5 + superbalota)
                if len(numeros) == 6 and tipo:
                    if fecha not in sorteos_por_fecha:
                        sorteos_por_fecha[fecha] = {}
                    
                    sorteos_por_fecha[fecha][tipo] = {
                        'n1': numeros[0], 'n2': numeros[1], 'n3': numeros[2],
                        'n4': numeros[3], 'n5': numeros[4],
                        'superbalota': numeros[5]
                    }
        
        # Convertir a lista de sorteos completos
        resultado = []
        for fecha, datos in sorteos_por_fecha.items():
            if 'baloto' in datos and 'revancha' in datos:
                baloto = datos['baloto']
                revancha = datos['revancha']
                
                resultado.append({
                    'fecha': fecha,
                    'n1': baloto['n1'], 'n2': baloto['n2'], 'n3': baloto['n3'],
                    'n4': baloto['n4'], 'n5': baloto['n5'],
                    'superbalota': baloto['superbalota'],
                    'rev1': revancha['n1'], 'rev2': revancha['n2'], 'rev3': revancha['n3'],
                    'rev4': revancha['n4'], 'rev5': revancha['n5'],
                    'rev_super': revancha['superbalota']
                })
            else:
                print(f"⚠️ Sorteo incompleto para {fecha}: {list(datos.keys())}")
        
        # Ordenar cronológicamente (la web devuelve del más reciente al más antiguo)
        resultado.reverse()
        return resultado
        
    except Exception as e:
        print(f"❌ Error al descargar: {e}")
        return []

def cargar_sorteos_existentes():
    """Carga las fechas de los sorteos ya existentes en el CSV"""
    fechas_existentes = set()
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            lector = csv.DictReader(f, delimiter=';')
            for fila in lector:
                fecha = fila.get('fecha', fila.get(' fecha', ''))
                if fecha:
                    fechas_existentes.add(fecha.strip())
    return fechas_existentes

def agregar_nuevos_sorteos(sorteos_nuevos):
    """Agrega los sorteos nuevos al final del CSV"""
    if not sorteos_nuevos:
        print("️ No hay sorteos nuevos para agregar.")
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
                'n1': s.get('n1', ''), 'n2': s.get('n2', ''), 
                'n3': s.get('n3', ''), 'n4': s.get('n4', ''), 
                'n5': s.get('n5', ''), 'n6': '',
                'superbalota': s.get('superbalota', ''),
                'rev1': s.get('rev1', ''), 'rev2': s.get('rev2', ''), 
                'rev3': s.get('rev3', ''), 'rev4': s.get('rev4', ''), 
                'rev5': s.get('rev5', ''), 'rev6': '',
                'rev_super': s.get('rev_super', ''),
                'revancha': 'sí' if s.get('rev1') else '',
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
    sorteos_web = obtener_sorteos()
    print(f"🌐 Sorteos descargados de la web: {len(sorteos_web)}")
    
    # 3. Filtrar solo los que no estén en el CSV
    nuevos = [s for s in sorteos_web if s['fecha'] not in fechas_existentes]
    print(f" Sorteos realmente nuevos: {len(nuevos)}")
    
    # 4. Agregar al CSV
    agregar_nuevos_sorteos(nuevos)
    
    print("✅ Proceso de actualización finalizado.")

if __name__ == "__main__":
    main()
