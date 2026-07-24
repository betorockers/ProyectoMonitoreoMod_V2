"""
Script de depuración limpia de consultas OSINT vía HTTP POST directo y BeautifulSoup.
Evita el uso de Selenium/Chromedriver y la ventana física.
"""
import os
import sys
import re
import requests
from bs4 import BeautifulSoup

def format_rut_with_dots(rut_raw: str) -> str:
    clean = re.sub(r'[^0-9kK]', '', str(rut_raw)).upper()
    if len(clean) < 2:
        return rut_raw
    body = clean[:-1]
    dv = clean[-1]
    formatted_body = "{:,}".format(int(body)).replace(",", ".")
    return f"{formatted_body}-{dv}"

def test_rut_direct(rut_val):
    print("\n--- TEST DIRECT HTTP RUT ---")
    rut_formatted = format_rut_with_dots(rut_val)
    print(f"Consultando RUT: {rut_formatted}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.nombrerutyfirma.com/",
        "Origin": "https://www.nombrerutyfirma.com"
    }
    
    # Probamos consultando por POST al endpoint de búsqueda
    url = "https://www.nombrerutyfirma.com/rut"
    payload = {"term": rut_formatted}
    
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        print(f"HTTP Status: {res.status_code}")
        
        # Analizar respuesta
        if "cloudflare" in res.text.lower() or "verify you are human" in res.text.lower():
            print("ALERT: Bloqueo de Cloudflare detectado en la llamada POST direct.")
            return False
            
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if table:
            tbody = table.find('tbody')
            if tbody:
                row = tbody.find('tr')
                if row:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        data = {
                            "Nombre": cells[0].text.strip(),
                            "RUT": cells[1].text.strip(),
                            "Sexo": cells[2].text.strip() if len(cells) > 2 else "",
                            "Dirección": cells[3].text.strip() if len(cells) > 3 else "",
                            "Ciudad/Comuna": cells[4].text.strip() if len(cells) > 4 else ""
                        }
                        print("SUCCESS: Datos de RUT recuperados:")
                        print(data)
                        return data
        print("FAIL: Tabla de resultados de RUT no encontrada en el HTML devuelto.")
        print(f"Cuerpo visible (primeros 400 chars): {soup.get_text()[:400].strip()}")
        return False
    except Exception as e:
        print(f"ERROR: Falló la petición a RUT: {str(e)}")
        return False

def test_ppu_direct(ppu_val):
    print("\n--- TEST DIRECT HTTP PPU ---")
    ppu_clean = re.sub(r'[^A-Za-z0-9]', '', str(ppu_val)).upper()
    print(f"Consultando PPU limpia: {ppu_clean}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.volanteomaleta.com/",
        "Origin": "https://www.volanteomaleta.com"
    }
    
    url = "https://www.volanteomaleta.com/patente"
    payload = {"term": ppu_clean}
    
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        print(f"HTTP Status: {res.status_code}")
        
        if "cloudflare" in res.text.lower() or "verify you are human" in res.text.lower() or "verificando la integridad" in res.text.lower():
            print("ALERT: Bloqueo de Cloudflare detectado en la llamada POST direct.")
            return False
            
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if table:
            thead = table.find('thead')
            tbody = table.find('tbody')
            if thead and tbody:
                headers_list = [th.text.strip() for th in thead.find_all(['th', 'td'])]
                row = tbody.find('tr')
                if row:
                    cells = [td.text.strip() for td in row.find_all('td')]
                    data = {}
                    for i in range(min(len(headers_list), len(cells))):
                        if headers_list[i]:
                            data[headers_list[i]] = cells[i]
                    print("SUCCESS: Datos de PPU recuperados:")
                    print(data)
                    return data
        print("FAIL: Tabla de resultados de PPU no encontrada en el HTML devuelto.")
        print(f"Cuerpo visible (primeros 400 chars): {soup.get_text()[:400].strip()}")
        return False
    except Exception as e:
        print(f"ERROR: Falló la petición a PPU: {str(e)}")
        return False

if __name__ == "__main__":
    test_rut_direct("16.691.169-9")
    test_ppu_direct("TYCC70")
