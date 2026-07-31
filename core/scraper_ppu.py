import re
import requests
from bs4 import BeautifulSoup


def scraper_ppu(ppu_input: str) -> list:
    """
    Scraper de PPU en volanteomaleta.com.
    Retorna todos los campos exactamente como los entrega el sitio:
    Patente, Tipo, Marca, Modelo, RUT, Nro. Motor, Año, Propietario
    """
    ppu_clean = re.sub(r'[^A-Za-z0-9]', '', str(ppu_input)).upper()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.volanteomaleta.com/",
        "Origin": "https://www.volanteomaleta.com",
    }

    url = "https://www.volanteomaleta.com/patente"
    payload = {"term": ppu_clean}

    try:
        res = requests.post(url, data=payload, headers=headers, timeout=12)
        if res.status_code != 200:
            return [("Error", f"Servidor externo respondió con código {res.status_code}", "", "", "", "", "", "")]

        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table")
        if not table:
            return [("Sin resultados", "Vehículo no encontrado en el registro.", "", "", "", "", "", "")]

        thead = table.find("thead")
        tbody = table.find("tbody")

        if not thead or not tbody:
            return [("Sin resultados", "Estructura de respuesta inesperada.", "", "", "", "", "", "")]

        # Leer cabeceras reales del sitio
        col_headers = [th.get_text(strip=True) for th in thead.find_all(["th", "td"])]

        results = []
        for row in tbody.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cells:
                continue
            # Mapear celdas a cabeceras de forma dinámica
            row_data = {}
            for i, header in enumerate(col_headers):
                row_data[header] = cells[i] if i < len(cells) else ""

            # Extraer los 8 campos en orden canónico
            patente    = row_data.get("Patente",           cells[0] if len(cells) > 0 else "")
            tipo       = row_data.get("Tipo",              cells[1] if len(cells) > 1 else "")
            marca      = row_data.get("Marca",             cells[2] if len(cells) > 2 else "")
            modelo     = row_data.get("Modelo",            cells[3] if len(cells) > 3 else "")
            rut_prop   = row_data.get("RUT",               cells[4] if len(cells) > 4 else "")
            nro_motor  = row_data.get("Nro. Motor",        cells[5] if len(cells) > 5 else "")
            anio       = row_data.get("Año",               cells[6] if len(cells) > 6 else "")
            propietario = row_data.get("Nombre a Rutificador", cells[7] if len(cells) > 7 else "")

            results.append((patente, tipo, marca, modelo, rut_prop, nro_motor, anio, propietario))

        return results if results else [("Sin resultados", "Vehículo no registrado.", "", "", "", "", "", "")]

    except requests.exceptions.Timeout:
        return [("Error", "Tiempo de espera agotado al conectar con volanteomaleta.com", "", "", "", "", "", "")]
    except Exception as e:
        return [("Error", f"Fallo al procesar PPU: {str(e)}", "", "", "", "", "", "")]
