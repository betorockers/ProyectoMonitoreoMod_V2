"""
Argos Guard Enterprise v4.0 - OSINT Automation & Scraping Service.

Motor de inteligencia con bypass de Cloudflare, anti-oclusión Chromium y dnspython.
"""
import os
import re
import random
import time
import shutil
import tempfile
import subprocess
import contextlib
import dns.resolver
from typing import Dict, Any, Optional

# Versi\u00f3n m\u00ednima de Chrome requerida. undetected-chromedriver intentar\u00e1 hacer match
# con la versi\u00f3n real instalada en el sistema. Este valor es el fallback si la
# autodetección falla. Actualizar si Chrome se actualiza a major > 136.
_CHROME_VERSION = 136

def format_rut_with_dots(rut_raw: str) -> str:
    """Formatea un RUT a su representación canónica con puntos y guion (e.g. 16.691.169-9)."""
    clean = re.sub(r'[^0-9kK]', '', str(rut_raw)).upper()
    if len(clean) < 2:
        return rut_raw
    body = clean[:-1]
    dv = clean[-1]
    formatted_body = "{:,}".format(int(body)).replace(",", ".")
    return f"{formatted_body}-{dv}"

def detect_chrome_executable() -> str:
    """Busca dinámicamente la ubicación física de Google Chrome en el sistema operativo Host."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe")
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return candidates[0]

@contextlib.contextmanager
def chromedriver_context():
    """Context Manager anti-oclusión con supresión de consola y purga automática."""
    import undetected_chromedriver as uc

    temp_dir = tempfile.mkdtemp(prefix="argos_uc_v4_")
    chrome_exe = detect_chrome_executable()

    options = uc.ChromeOptions()
    options.binary_location = chrome_exe
    options.add_argument("--window-position=-32000,-32000")
    options.add_argument("--disable-features=CalculateNativeWinOcclusion,WinUseNativeTitlebar,CalculateNativeWinOcclusion")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")

    driver = None
    try:
        driver = uc.Chrome(
            options=options,
            version_main=_CHROME_VERSION,
            user_data_dir=temp_dir,
            suppress_welcome=True,
            use_subprocess=True
        )
        if os.name == 'nt':
            try:
                import win32gui, win32con
                hwnd = driver.service.process.pid if hasattr(driver.service, 'process') else None
                if hwnd:
                    win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, -32000, -32000, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
            except Exception:
                pass
        yield driver
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        shutil.rmtree(temp_dir, ignore_errors=True)

def scrape_rut(rut_input: str) -> Dict[str, Any]:
    """Scraper de RUT en nombrerutyfirma.com."""
    rut_formatted = format_rut_with_dots(rut_input)
    with chromedriver_context() as driver:
        driver.get("https://www.nombrerutyfirma.com/")
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//form[contains(@action, 'rut')]//input[@name='term']"))
            )
            driver.execute_script("arguments[0].value = arguments[1];", search_box, rut_formatted)

            submit_btn = driver.find_element(By.XPATH, "//form[contains(@action, 'rut')]//button[@type='submit']")
            driver.execute_script("arguments[0].click();", submit_btn)

            try:
                rows = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//table//tr[td]"))
                )
            except Exception:
                return {"error": "RUT no encontrado en el registro nacional."}

            cells = rows[0].find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                return {
                    "Nombre": cells[0].text.strip(),
                    "RUT": cells[1].text.strip()
                }
        except Exception as e:
            return {"error": f"Fallo al procesar RUT: {str(e)}"}
    return {"error": "Sin datos retornados"}

def scrape_ppu(ppu_input: str) -> Dict[str, Any]:
    """Scraper de PPU en volanteomaleta.com / patentechile.com."""
    ppu_clean = re.sub(r'[^A-Za-z0-9]', '', str(ppu_input)).upper()
    with chromedriver_context() as driver:
        driver.get("https://www.volanteomaleta.com/")
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div/div[1]/form/div/input"))
            )
            search_box.clear()
            for char in ppu_clean:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.02, 0.05))

            btn = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[1]/form/div/span/button")
            btn.click()

            result_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div"))
            )
            table = WebDriverWait(result_container, 5).until(
                EC.presence_of_element_located((By.XPATH, ".//table[contains(@class, 'table')]"))
            )
            headers = [th.text.strip() for th in table.find_elements(By.XPATH, ".//thead/tr/th")]
            row = table.find_element(By.XPATH, ".//tbody/tr")
            cells = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
            
            data = {}
            for i in range(min(len(headers), len(cells))):
                if headers[i]:
                    data[headers[i]] = cells[i]
            if data:
                return data
            return {"error": "Vehículo no registrado en el sistema."}
        except Exception as e:
            return {"error": f"Fallo al procesar PPU: {str(e)}"}

def resolve_dns_records(domain: str) -> Dict[str, Any]:
    """Resolución nativa de registros DNS con dnspython v2.8.0."""
    result = {}
    record_types = ['A', 'MX', 'TXT', 'NS', 'SOA']
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            result[rtype] = ", ".join([str(rdata) for rdata in answers])
        except Exception:
            result[rtype] = "No encontrado"
    return result

# ==========================================
# NUEVOS MÓDULOS OSINT & INTELIGENCIA (11)
# ==========================================

import requests
import json
import socket
try:
    import whois
except ImportError:
    whois = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from apps.core.models import ApiKeyConfig

def query_geografia(city: str) -> Dict[str, Any]:
    """Obtiene clima y coordenadas usando Open-Meteo Geocoding y Weather API."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=es&format=json"
        geo_res = requests.get(geo_url, timeout=10).json()
        if not geo_res.get("results"):
            return {"error": f"No se encontró la ciudad '{city}'."}
        
        loc = geo_res["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        w_res = requests.get(weather_url, timeout=10).json()
        
        current = w_res.get("current_weather", {})
        return {
            "Ciudad": loc.get("name"),
            "Región/País": f"{loc.get('admin1', '')}, {loc.get('country', '')}",
            "Coordenadas": f"{lat}, {lon}",
            "Temperatura": f"{current.get('temperature', 'N/A')} °C",
            "Velocidad Viento": f"{current.get('windspeed', 'N/A')} km/h",
            "Código Clima": str(current.get('weathercode', 'N/A'))
        }
    except Exception as e:
        return {"error": f"Fallo al consultar geografía: {str(e)}"}

def query_fugas(email: str) -> Dict[str, Any]:
    """Busca fugas de datos de un email."""
    try:
        # Check HIBP api key
        key_obj = ApiKeyConfig.objects.filter(service='hibp', is_active=True).first()
        if key_obj and key_obj.api_key:
            headers = {
                'hibp-api-key': key_obj.api_key,
                'user-agent': 'ArgosGuard-v4'
            }
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                breaches = res.json()
                return {
                    "Email": email,
                    "Total Fugas": len(breaches),
                    "Brechas Detectadas": ", ".join([b.get('Name') for b in breaches[:10]])
                }
            elif res.status_code == 404:
                return {"Resultado": f"Felicidades, el email {email} no registra fugas conocidas (HIBP)."}
            else:
                return {"error": f"Error HIBP: {res.status_code}"}
        else:
            return {"error": "No hay API Key configurada para Have I Been Pwned. Configúrela en el panel de Configuración."}
    except Exception as e:
        return {"error": f"Fallo al consultar fugas: {str(e)}"}

def query_reputacion(ip: str) -> Dict[str, Any]:
    """Consulta reputación de IP en AbuseIPDB."""
    try:
        key_obj = ApiKeyConfig.objects.filter(service='abuseipdb', is_active=True).first()
        if key_obj and key_obj.api_key:
            headers = {
                'Key': key_obj.api_key,
                'Accept': 'application/json'
            }
            url = "https://api.abuseipdb.com/api/v2/check"
            params = {'ipAddress': ip, 'maxAgeInDays': 90}
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json().get('data', {})
                return {
                    "IP": data.get('ipAddress'),
                    "Confianza de Abuso": f"{data.get('abuseConfidenceScore', 0)}%",
                    "Total Reportes": data.get('totalReports', 0),
                    "ISP": data.get('isp'),
                    "País": data.get('countryCode')
                }
            return {"error": f"Error AbuseIPDB: {res.status_code}"}
        else:
            return {"error": "API Key de AbuseIPDB no configurada."}
    except Exception as e:
        return {"error": f"Fallo al consultar reputación: {str(e)}"}

def query_infra(target: str) -> Dict[str, Any]:
    """Consulta infraestructura en Shodan."""
    try:
        key_obj = ApiKeyConfig.objects.filter(service='shodan', is_active=True).first()
        if key_obj and key_obj.api_key:
            url = f"https://api.shodan.io/shodan/host/{target}?key={key_obj.api_key}"
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                data = res.json()
                ports = data.get('ports', [])
                return {
                    "IP": data.get('ip_str'),
                    "Organización": data.get('org', 'N/A'),
                    "OS Detectado": data.get('os', 'Desconocido'),
                    "Puertos Expuestos": ", ".join(map(str, ports)),
                    "Vulnerabilidades": ", ".join(data.get('vulns', [])) if data.get('vulns') else "Ninguna detectada"
                }
            elif res.status_code == 404:
                return {"Resultado": f"No hay información en Shodan para {target}"}
            else:
                return {"error": f"Error Shodan: {res.status_code}"}
        else:
            return {"error": "API Key de Shodan no configurada."}
    except Exception as e:
        return {"error": f"Fallo al consultar infraestructura: {str(e)}"}

def query_whois(domain: str) -> Dict[str, Any]:
    """Consulta de registro WHOIS nativo."""
    if not whois:
        return {"error": "La librería python-whois no está instalada."}
    try:
        w = whois.whois(domain)
        return {
            "Dominio": w.domain_name if isinstance(w.domain_name, str) else str(w.domain_name),
            "Registrante": w.registrar,
            "Creación": str(w.creation_date),
            "Expiración": str(w.expiration_date),
            "Organización": w.org if w.org else "Oculto/Privado",
            "Nameservers": ", ".join(w.name_servers) if w.name_servers else "N/A"
        }
    except Exception as e:
        return {"error": f"Fallo al consultar WHOIS: {str(e)}"}

def query_ipgeo(ip: str) -> Dict[str, Any]:
    """Geolocalización de IP y ASN."""
    try:
        url = f"http://ip-api.com/json/{ip}"
        res = requests.get(url, timeout=10).json()
        if res.get("status") == "success":
            return {
                "IP": res.get("query"),
                "País": res.get("country"),
                "Ciudad": res.get("city"),
                "ISP / Org": res.get("isp"),
                "Latitud": res.get("lat"),
                "Longitud": res.get("lon"),
                "ASN": res.get("as")
            }
        return {"error": res.get("message", "Error desconocido")}
    except Exception as e:
        return {"error": f"Fallo al geolocalizar IP: {str(e)}"}

def query_web(url: str) -> Dict[str, Any]:
    """Analizador Web Básico (Headers y Meta)."""
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        res = requests.get(url, timeout=10, verify=False)
        headers = res.headers
        data = {
            "URL": res.url,
            "Status Code": res.status_code,
            "Servidor (Server)": headers.get("Server", "Oculto"),
            "X-Powered-By": headers.get("X-Powered-By", "Oculto"),
            "Content-Type": headers.get("Content-Type", "N/A")
        }
        if BeautifulSoup:
            soup = BeautifulSoup(res.text, 'lxml')
            title = soup.title.string if soup.title else "Sin Título"
            data["Título HTML"] = title.strip()
        return data
    except Exception as e:
        return {"error": f"Fallo al analizar web: {str(e)}"}

def query_puertos(target: str) -> Dict[str, Any]:
    """Escaneo NMAP nativo o fallback a Socket."""
    try:
        # Intento con nmap.exe
        result = subprocess.run(["nmap", "-Pn", "-p", "21,22,25,80,443,3306,3389,8080", target], 
                                capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            open_ports = []
            for line in lines:
                if "/tcp" in line and "open" in line:
                    open_ports.append(line.strip())
            return {
                "Target": target,
                "Motor": "Nmap nativo",
                "Puertos Abiertos": ", ".join(open_ports) if open_ports else "Ninguno de los críticos"
            }
    except Exception:
        pass # Fallback to sockets

    # Socket fallback
    common_ports = [21, 22, 25, 80, 443, 3306, 3389, 8080]
    open_ports = []
    for port in common_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((target, port))
        if result == 0:
            open_ports.append(str(port))
        sock.close()
    
    return {
        "Target": target,
        "Motor": "Python Socket (Fallback)",
        "Puertos Críticos Abiertos": ", ".join(open_ports) if open_ports else "Ninguno"
    }

def query_subdominios(domain: str) -> Dict[str, Any]:
    """Busca subdominios indexados en crt.sh (Certificate Transparency)."""
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            subs = set()
            for entry in data:
                subs.add(entry.get('name_value', '').lower())
            return {
                "Dominio Raíz": domain,
                "Total Subdominios": len(subs),
                "Muestra (Max 15)": ", ".join(list(subs)[:15])
            }
        return {"error": f"Error crt.sh: {res.status_code}"}
    except Exception as e:
        return {"error": f"Fallo al buscar subdominios: {str(e)}"}

def query_email(email: str) -> Dict[str, Any]:
    """Valida sintaxis y busca registros MX del dominio del email."""
    if "@" not in email:
        return {"error": "Sintaxis de email inválida"}
    domain = email.split("@")[1]
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = [str(rdata.exchange) for rdata in answers]
        return {
            "Email": email,
            "Dominio": domain,
            "Registros MX": ", ".join(mx_records),
            "Veredicto": "El dominio puede recibir correos (MX Válido)."
        }
    except Exception as e:
        return {"error": f"No se encontraron registros MX para {domain} ({str(e)})"}

def query_traceroute(target: str) -> Dict[str, Any]:
    """Ejecuta tracert (Windows) limitando a 15 saltos."""
    try:
        cmd = ["tracert", "-d", "-h", "15", "-w", "1000", target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25, encoding='cp850', errors='ignore')
        lines = result.stdout.split('\n')
        hops = [line.strip() for line in lines if " ms " in line or "*" in line]
        return {
            "Target": target,
            "Saltos Capturados": len(hops),
            "Traza": " | ".join(hops[:5]) + ("..." if len(hops)>5 else "")
        }
    except Exception as e:
        return {"error": f"Fallo al trazar ruta: {str(e)}"}
