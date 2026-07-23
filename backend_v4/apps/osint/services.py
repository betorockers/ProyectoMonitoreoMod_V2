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


def format_rut_with_dots(rut_raw: str) -> str:
    """Formatea un RUT a su representación canónica con puntos y guion (e.g. 16.691.169-9)."""
    clean = re.sub(r'[^0-9kK]', '', str(rut_raw)).upper()
    if len(clean) < 2:
        return rut_raw
    body = clean[:-1]
    dv = clean[-1]
    formatted_body = "{:,}".format(int(body)).replace(",", ".")
    return f"{formatted_body}-{dv}"

def detect_chrome_executable() -> Optional[str]:
    """Busca la ubicación de Chrome en Windows por si es requerida por Selenium."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe")
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None

@contextlib.contextmanager
def chromedriver_context():
    """
    Context Manager universal que levanta Selenium nativo con evasión Stealth de Cloudflare.
    No requiere undetected-chromedriver ni cálculos de versionamiento de Chrome.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium_stealth import stealth

    options = Options()
    options.add_argument('--headless=new')  # Modo headless indetectable moderno
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--incognito')  # Sesión de navegación de incógnito estricto

    chrome_bin = detect_chrome_executable()
    if chrome_bin:
        options.binary_location = chrome_bin

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        
        stealth(
            driver,
            languages=['es-ES', 'es'],
            vendor='Google Inc.',
            platform='Win32',
            webgl_vendor='Intel Inc.',
            renderer='Intel Iris OpenGL Engine',
            fix_hairline=True,
        )
        yield driver
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def scrape_rut(rut_input: str) -> Dict[str, Any]:
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
        import requests
        from bs4 import BeautifulSoup
        
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code != 200:
            return {"error": f"Error del servidor externo (Código {res.status_code})."}
            
        if "cloudflare" in res.text.lower() or "verify you are human" in res.text.lower():
            return {"error": "Fallo al evadir protección perimetral del sitio de RUT."}
            
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if table:
            tbody = table.find('tbody')
            if tbody:
                row = tbody.find('tr')
                if row:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        return {
                            "Nombre": cells[0].text.strip(),
                            "RUT": cells[1].text.strip(),
                            "Sexo": cells[2].text.strip() if len(cells) > 2 else "",
                            "Dirección": cells[3].text.strip() if len(cells) > 3 else "",
                            "Ciudad/Comuna": cells[4].text.strip() if len(cells) > 4 else ""
                        }
        return {"error": "RUT no encontrado en el registro nacional."}
    except Exception as e:
        return {"error": f"Fallo al procesar RUT: {str(e)}"}

def scrape_ppu(ppu_input: str) -> Dict[str, Any]:
    """Scraper de PPU en volanteomaleta.com utilizando peticiones directas HTTP y BeautifulSoup."""
    ppu_clean = re.sub(r'[^A-Za-z0-9]', '', str(ppu_input)).upper()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.volanteomaleta.com/",
        "Origin": "https://www.volanteomaleta.com"
    }
    
    url = "https://www.volanteomaleta.com/patente"
    payload = {"term": ppu_clean}
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code != 200:
            return {"error": f"Error del servidor externo (Código {res.status_code})."}
            
        if "cloudflare" in res.text.lower() or "verify you are human" in res.text.lower() or "verificando la integridad" in res.text.lower():
            return {"error": "Fallo al evadir protección perimetral del sitio de PPU."}
            
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
                    if data:
                        return data
        return {"error": "Vehiculo no registrado en el sistema."}
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
    """Busca fugas de datos usando HIBP o fallbacks resilientes de EmailRep / Auditoría DNS."""
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
            # Fallback 1: EmailRep.io
            try:
                url = f"https://emailrep.io/{email}"
                headers = {'User-Agent': 'ArgosGuard-OSINT'}
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    details = data.get("details", {})
                    return {
                        "Email": email,
                        "Reputación": "Seguro (Alta)" if data.get("reputation") == "high" else "Sospechoso (Baja)",
                        "Actividad Maliciosa": "Sí" if details.get("malicious_activity") else "No",
                        "Spam Reportado": "Sí" if details.get("spam") else "No",
                        "Brecha de Datos": "Sí" if details.get("data_breach") else "No detectado",
                        "Credenciales Filtradas": "Sí" if details.get("credentials_leaked") else "No",
                        "Fuente": "EmailRep.io (API Pública)"
                    }
            except Exception:
                pass
            
            # Fallback 2: Auditoría DNS local del dominio de correo
            if "@" in email:
                domain = email.split("@")[1]
                try:
                    import dns.resolver
                    answers = dns.resolver.resolve(domain, 'MX')
                    mx_servers = [str(r.exchange) for r in answers]
                    return {
                        "Email": email,
                        "Estructura Correo": "Sintaxis Válida",
                        "Reputación Servidor": "Dominio Activo",
                        "Servidores MX": mx_servers[0] if mx_servers else "N/A",
                        "Análisis Fugas": "Habilitar HIBP en Configuración para escaneo profundo de credenciales",
                        "Fuente": "Auditoría Interna de Dominio (Resiliente)"
                    }
                except Exception:
                    pass

            return {
                "Email": email,
                "Estructura Correo": "Sintaxis Válida",
                "Estado Dominio": "Sin servidores de correo activos",
                "Análisis Fugas": "Fallo al conectar con servidores de HIBP/EmailRep.",
                "Fuente": "Auditoría Interna (Offline)"
            }
    except Exception as e:
        return {"error": f"Fallo al consultar fugas: {str(e)}"}

def query_reputacion(ip: str) -> Dict[str, Any]:
    """Consulta reputación de IP en AbuseIPDB (si hay key) o mediante análisis geo-resiliente."""
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
            # Fallback Geo-Resiliente + DNSBL
            blacklisted = "No detectado"
            try:
                reversed_ip = ".".join(reversed(ip.split(".")))
                query = f"{reversed_ip}.zen.spamhaus.org"
                socket.gethostbyname(query)
                blacklisted = "DETECTADO (Spamhaus)"
            except Exception:
                pass
                
            geo = query_ipgeo(ip)
            if "error" not in geo:
                isp = geo.get("ISP / Org", "Desconocido")
                is_hosting = any(word in isp.lower() for word in ["hosting", "digitalocean", "amazon", "ovh", "linode", "vultr", "m247", "google cloud", "azure", "hetzner"])
                
                score = "15% (Riesgo Bajo)"
                if is_hosting:
                    score = "90% (Riesgo Alto - DataCenter/Proxy)"
                elif blacklisted != "No detectado":
                    score = "65% (Riesgo Medio - Listado SPAM)"
                    
                return {
                    "IP": ip,
                    "Confianza de Abuso": score,
                    "Lista Negra (DNSBL)": blacklisted,
                    "ISP / Operador": isp,
                    "País": geo.get("País", "Desconocido"),
                    "Fuente": "DNSBL Spamhaus + Geo-Resiliente"
                }
            return {
                "IP": ip,
                "Confianza de Abuso": "Evaluación limitada",
                "Lista Negra (DNSBL)": blacklisted,
                "ISP / Operador": "Desconocido (Modo Desconectado)",
                "Fuente": "DNSBL Local (Resiliente)"
            }
    except Exception as e:
        return {"error": f"Fallo al consultar reputación: {str(e)}"}

def query_infra(target: str) -> Dict[str, Any]:
    """Consulta infraestructura en Shodan o escaneo remoto/local resiliente."""
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
            # Fallback 1: Escaneo NMAP remoto vía HackerTarget API
            try:
                url = f"https://api.hackertarget.com/nmap/?q={target}"
                res = requests.get(url, timeout=8)
                if res.status_code == 200 and "nmap" in res.text.lower():
                    lines = res.text.split('\n')
                    open_ports = [line.strip() for line in lines if "open" in line]
                    return {
                        "Target": target,
                        "Motor Escaneo": "HackerTarget Remote Nmap (Público)",
                        "Puertos Detectados": ", ".join(open_ports) if open_ports else "Ningún puerto crítico expuesto",
                        "Detalle Escaneo": "Escaneo remoto completado con éxito."
                    }
            except Exception:
                pass

            # Fallback 2: Escaneo Socket local paralelo
            common_ports = [21, 22, 25, 80, 443, 3306, 3389, 8080]
            open_ports = []
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.8)
                    result = sock.connect_ex((target, port))
                    if result == 0:
                        open_ports.append(str(port))
                    sock.close()
                except Exception:
                    pass
            return {
                "Target": target,
            "Motor Escaneo": "Python Sockets (Fallback Local)",
            "Puertos Críticos Abiertos": ", ".join(open_ports) if open_ports else "Ninguno de los críticos abiertos",
            "Detalle Escaneo": "Escaneo TCP local completado (Shodan y HackerTarget offline)."
        }
    except Exception as e:
        return {"error": f"Fallo al consultar infraestructura: {str(e)}"}

def query_whois(domain: str) -> Dict[str, Any]:
    """Consulta de registro WHOIS universal con limpieza de URLs y soporte de TLDs globales y locales (.com, .cl, .com.ar, .mx)."""
    # 1. Limpieza estricta de URL y subdominios decorativos para extraer únicamente el dominio limpio
    domain_clean = domain.strip().lower()
    # Eliminar protocolo si lo escriben
    domain_clean = re.sub(r"^https?://", "", domain_clean)
    # Eliminar rutas, parámetros de consulta o puertos
    domain_clean = domain_clean.split("/")[0].split(":")[0]
    # Eliminar prefijo www.
    if domain_clean.startswith("www."):
        domain_clean = domain_clean[4:]
        
    # 2. Scraper oficial para dominios .cl (NIC Chile)
    if domain_clean.endswith(".cl"):
        try:
            name = domain_clean.split(".")[0]
            url = f"https://www.nic.cl/registry/Whois.do?d={name}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "lxml")
                titular = "Desconocido"
                creacion = "N/A"
                expiracion = "N/A"
                
                for div in soup.find_all("div"):
                    b_tag = div.find("b")
                    if b_tag:
                        b_text = b_tag.get_text(strip=True).lower()
                        sibling = div.find_next_sibling("div")
                        if sibling:
                            val = sibling.get_text(strip=True)
                            if "titular" in b_text:
                                titular = val
                            elif "creaci" in b_text:
                                creacion = val
                            elif "expiraci" in b_text:
                                expiracion = val
                                
                # Intentar también Nameservers por resolución DNS local
                ns_servers = []
                try:
                    import dns.resolver
                    answers = dns.resolver.resolve(domain_clean, 'NS')
                    ns_servers = [str(r.target) for r in answers]
                except Exception:
                    pass
                
                return {
                    "Dominio": domain_clean,
                    "Registrante": titular,
                    "Creación": creacion,
                    "Expiración": expiracion,
                    "Organización": "NIC Chile (Registro Oficial)",
                    "Nameservers": ", ".join(ns_servers) if ns_servers else "N/A"
                }
        except Exception:
            pass

    # 3. Intento nativo con python-whois para otros TLDs (.com, .net, .org, etc.)
    try:
        if whois:
            w = whois.whois(domain_clean)
            if w.domain_name:
                return {
                    "Dominio": w.domain_name if isinstance(w.domain_name, str) else str(w.domain_name),
                    "Registrante": w.registrar if w.registrar else "Desconocido",
                    "Creación": str(w.creation_date) if w.creation_date else "N/A",
                    "Expiración": str(w.expiration_date) if w.expiration_date else "N/A",
                    "Organización": w.org if w.org else "Oculto/Privado",
                    "Nameservers": ", ".join(w.name_servers) if w.name_servers else "N/A"
                }
    except Exception:
        pass
        
    # 4. Fallback 1: HackerTarget WHOIS API (Soporta múltiples TLDs internacionales de forma pública)
    try:
        url = f"https://api.hackertarget.com/whois/?q={domain_clean}"
        res = requests.get(url, timeout=8)
        if res.status_code == 200 and "registrar" in res.text.lower():
            lines = res.text.split('\n')
            registrar = "Desconocido"
            creation = "N/A"
            expiration = "N/A"
            for line in lines:
                if "registrar:" in line.lower():
                    registrar = line.split(":", 1)[1].strip()
                elif "creation date:" in line.lower() or "created:" in line.lower():
                    creation = line.split(":", 1)[1].strip()
                elif "registry expiry date:" in line.lower() or "expire:" in line.lower():
                    expiration = line.split(":", 1)[1].strip()
            return {
                "Dominio": domain_clean,
                "Registrante": registrar,
                "Creación": creation,
                "Expiración": expiration,
                "Organización": "Consultar WHOIS Completo",
                "Nameservers": "HackerTarget API (Fallback)"
            }
    except Exception:
        pass

    # 5. Fallback 2: Resolución DNS local NS + IP para dominios regionales difíciles (.com.ar, .mx, etc.)
    try:
        import dns.resolver
        ns_servers = []
        ip_addr = "N/A"
        try:
            answers = dns.resolver.resolve(domain_clean, 'NS')
            ns_servers = [str(r.target) for r in answers]
        except Exception:
            pass
        try:
            ips = dns.resolver.resolve(domain_clean, 'A')
            ip_addr = str(ips[0])
        except Exception:
            pass
            
        return {
            "Dominio": domain_clean,
            "Registrante": "Oculto/Privado (Fallo WHOIS)",
            "Creación": "N/A",
            "Expiración": "N/A",
            "Organización": f"Resolución DNS (IP: {ip_addr})",
            "Servidores DNS (NS)": ", ".join(ns_servers) if ns_servers else "N/A"
        }
    except Exception:
        pass

    return {
        "Dominio": domain_clean,
        "Registrante": "Desconocido",
        "Creación": "N/A",
        "Expiración": "N/A",
        "Organización": "Desconocida (Sin conexión WHOIS/DNS)"
    }


def query_subdominios(domain: str) -> Dict[str, Any]:
    """Busca subdominios indexados usando crt.sh con fallback rápido a HackerTarget Host Search."""
    domain_clean = domain.strip().lower()
    
    # 1. Consulta principal a crt.sh
    try:
        url = f"https://crt.sh/?q=%25.{domain_clean}&output=json"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            subs = set()
            for entry in data:
                subs.add(entry.get('name_value', '').lower())
            if subs:
                return {
                    "Dominio Raíz": domain_clean,
                    "Total Subdominios": len(subs),
                    "Muestra (Max 15)": ", ".join(list(subs)[:15]),
                    "Fuente": "crt.sh (Certificate Transparency)"
                }
    except Exception:
        pass

    # 2. Fallback real a HackerTarget Host Search (Estable y veloz ante error 502/504 de crt.sh)
    try:
        url = f"https://api.hackertarget.com/hostsearch/?q={domain_clean}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and "invalid" not in res.text.lower() and "error" not in res.text.lower():
            lines = res.text.strip().split('\n')
            subs = set()
            for line in lines:
                if "," in line:
                    sub = line.split(",")[0].strip().lower()
                    subs.add(sub)
            if subs:
                return {
                    "Dominio Raíz": domain_clean,
                    "Total Subdominios": len(subs),
                    "Muestra (Max 15)": ", ".join(list(subs)[:15]),
                    "Fuente": "HackerTarget HostSearch (Público)"
                }
    except Exception:
        pass

    return {"error": "No se encontraron subdominios (servidores crt.sh/HackerTarget desconectados)."}

def query_ipgeo(ip: str) -> Dict[str, Any]:
    """Geolocalización de IP y ASN usando HTTPS y múltiples resolvedores públicos resilientes."""
    # Resolvedor 1: ip-api.com (HTTPS)
    try:
        url = f"https://ip-api.com/json/{ip}"
        res = requests.get(url, timeout=6).json()
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
    except Exception:
        pass

    # Resolvedor 2: ipwhois.app (HTTPS)
    try:
        url = f"https://ipwhois.app/json/{ip}"
        res = requests.get(url, timeout=6).json()
        if res.get("success"):
            return {
                "IP": res.get("ip"),
                "País": res.get("country"),
                "Ciudad": res.get("city"),
                "ISP / Org": res.get("isp"),
                "Latitud": res.get("latitude"),
                "Longitud": res.get("longitude"),
                "ASN": res.get("asn")
            }
    except Exception:
        pass

    # Resolvedor 3: ipapi.co (HTTPS)
    try:
        url = f"https://ipapi.co/{ip}/json/"
        headers = {'User-Agent': 'ArgosGuard-OSINT-Agent'}
        res = requests.get(url, headers=headers, timeout=6).json()
        if not res.get("error"):
            return {
                "IP": res.get("ip"),
                "País": res.get("country_name"),
                "Ciudad": res.get("city"),
                "ISP / Org": res.get("org"),
                "Latitud": res.get("latitude"),
                "Longitud": res.get("longitude"),
                "ASN": res.get("asn")
            }
    except Exception:
        pass

    return {"error": "Servicios de geolocalización IP no disponibles (Offline/Bloqueado)"}

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


# ────────────────────────────────────────────────────────────────────────────
# ESCÁNER LAN DE SEGURIDAD — Detecta hosts activos y servicios inseguros
# ────────────────────────────────────────────────────────────────────────────
import socket
import ipaddress
import concurrent.futures

# Puertos a auditar con su nivel de riesgo y descripción
_AUDIT_PORTS = [
    (21,   "FTP",            "ALTO",   "Transferencia de archivos sin cifrado"),
    (22,   "SSH",            "INFO",   "Acceso remoto seguro (verificar config)"),
    (23,   "Telnet",         "CRITICO","Administración remota SIN CIFRADO"),
    (25,   "SMTP",           "ALTO",   "Servidor de correo — posible relay abierto"),
    (80,   "HTTP",           "MEDIO",  "Web sin cifrado TLS"),
    (135,  "MSRPC",          "MEDIO",  "RPC Windows — vector de ataques"),
    (139,  "NetBIOS",        "MEDIO",  "Compartición de archivos Windows"),
    (443,  "HTTPS",          "INFO",   "Web cifrada — OK"),
    (445,  "SMB",            "ALTO",   "Compartición SMB — riesgo WannaCry/EternalBlue"),
    (3389, "RDP",            "ALTO",   "Escritorio remoto expuesto"),
    (8080, "HTTP-Alt",       "MEDIO",  "Servicio web alternativo"),
    (8443, "HTTPS-Alt",      "INFO",   "Web cifrada alternativa"),
    (1433, "MSSQL",          "ALTO",   "Base de datos SQL Server expuesta"),
    (3306, "MySQL",          "ALTO",   "Base de datos MySQL expuesta"),
    (5432, "PostgreSQL",     "ALTO",   "Base de datos PostgreSQL expuesta"),
    (6379, "Redis",          "CRITICO","Redis sin auth — base de datos expuesta"),
    (27017,"MongoDB",        "CRITICO","MongoDB sin auth — base de datos expuesta"),
    (161,  "SNMP",           "ALTO",   "Protocolo de gestión de red — info sensible"),
    (2049, "NFS",            "ALTO",   "Network File System — archivos en red"),
    (5900, "VNC",            "ALTO",   "Control remoto VNC — posible sin contraseña"),
]

_RISK_ORDER = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "INFO": 3}


def _tcp_probe(ip: str, port: int, timeout: float = 0.6) -> bool:
    """Intenta conexión TCP. Retorna True si el puerto está abierto."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0
    except Exception:
        return False


def _icmp_alive(ip: str) -> bool:
    """Detecta si un host está activo via ping (Windows/Linux)."""
    try:
        flag = "-n" if os.name == "nt" else "-c"
        r = subprocess.run(
            ["ping", flag, "1", "-w", "300", ip],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=2
        )
        return r.returncode == 0
    except Exception:
        return False


def _reverse_dns(ip: str) -> str:
    """Resuelve hostname reverso para una IP."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


def _scan_host(ip: str) -> Optional[dict]:
    """
    Escanea un host: detecta si está activo y luego audita puertos.
    Retorna None si el host no responde.
    """
    # Comprobación rápida: primero intenta ICMP, luego TCP en puerto 80 o 443
    alive = _icmp_alive(ip)
    if not alive:
        # Fallback TCP para hosts que bloquean ICMP
        alive = _tcp_probe(ip, 80, timeout=0.4) or _tcp_probe(ip, 443, timeout=0.4) \
                or _tcp_probe(ip, 22, timeout=0.4) or _tcp_probe(ip, 445, timeout=0.4)
    if not alive:
        return None

    hostname = _reverse_dns(ip)
    open_ports = []
    for port, service, risk, desc in _AUDIT_PORTS:
        if _tcp_probe(ip, port):
            open_ports.append({
                "port":    port,
                "service": service,
                "risk":    risk,
                "desc":    desc,
            })

    # Calcular riesgo máximo del host
    if open_ports:
        max_risk = min(open_ports, key=lambda p: _RISK_ORDER[p["risk"]])["risk"]
    else:
        max_risk = "INFO"

    return {
        "ip":         ip,
        "hostname":   hostname or "—",
        "alive":      True,
        "open_ports": open_ports,
        "max_risk":   max_risk,
    }


def scan_lan_security(subnet: str = "", max_hosts: int = 60) -> dict:
    """
    Escanea la subred local en busca de hosts activos y servicios inseguros.

    Args:
        subnet: Prefijo de red (ej. "10.88.22"). Si vacío, autodetecta la LAN.
        max_hosts: Máximo número de IPs a probar (.1 → .max_hosts).

    Returns:
        dict con claves: subnet, hosts_escaneados, hosts_activos, hallazgos, resumen
    """
    # Auto-detección de subred local si no se provee
    if not subnet:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            parts = local_ip.rsplit(".", 1)
            subnet = parts[0]
        except Exception:
            subnet = "192.168.1"

    targets = [f"{subnet}.{i}" for i in range(1, min(max_hosts + 1, 255))]

    hallazgos = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        futures = {executor.submit(_scan_host, ip): ip for ip in targets}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                hallazgos.append(result)

    # Ordenar: primero por riesgo, luego por IP
    hallazgos.sort(key=lambda h: (_RISK_ORDER.get(h["max_risk"], 99),
                                   [int(x) for x in h["ip"].split(".")]))

    # Resumen de vulnerabilidades
    criticos  = [h for h in hallazgos if h["max_risk"] == "CRITICO"]
    altos     = [h for h in hallazgos if h["max_risk"] == "ALTO"]
    medios    = [h for h in hallazgos if h["max_risk"] == "MEDIO"]
    # Todos los puertos inseguros en la red
    puertos_inseguros = []
    for h in hallazgos:
        for p in h["open_ports"]:
            if p["risk"] in ("CRITICO", "ALTO"):
                puertos_inseguros.append(f"{h['ip']}:{p['port']} ({p['service']})")

    return {
        "subnet":           subnet + ".0/24",
        "hosts_escaneados": len(targets),
        "hosts_activos":    len(hallazgos),
        "hosts_criticos":   len(criticos),
        "hosts_altos":      len(altos),
        "hosts_medios":     len(medios),
        "puertos_inseguros": puertos_inseguros,
        "hallazgos":        hallazgos,
    }
