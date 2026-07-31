import re
import requests
from bs4 import BeautifulSoup

def format_rut_with_dots(rut_raw: str) -> str:
    """Formatea un RUT a su representación canónica con puntos y guion (e.g. 16.691.169-9)."""
    clean = re.sub(r'[^0-9kK]', '', str(rut_raw)).upper()
    if len(clean) < 2:
        return rut_raw
    body = clean[:-1]
    dv = clean[-1]
    formatted_body = "{:,}".format(int(body)).replace(",", ".")
    return f"{formatted_body}-{dv}"

def scraper_rut(rut_input: str) -> list:
    """Scraper de RUT en nombrerutyfirma.com utilizando peticiones directas HTTP y BeautifulSoup."""
    rut_formatted = format_rut_with_dots(rut_input)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.nombrerutyfirma.com/",
        "Origin": "https://www.nombrerutyfirma.com"
    }
    
    url = "https://www.nombrerutyfirma.com/rut"
    payload = {"term": rut_formatted}
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code != 200:
            return [("Error", f"Error del servidor (Código {res.status_code})")]
        
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if table:
            tbody = table.find('tbody')
            if tbody:
                row = tbody.find('tr')
                if row:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Return ONLY RUT and Name as requested previously
                        return [(cells[1].text.strip(), cells[0].text.strip())]
        return [("Error", "RUT no encontrado en el registro nacional.")]
    except Exception as e:
        return [("Error", f"Fallo al procesar RUT: {str(e)}")]
