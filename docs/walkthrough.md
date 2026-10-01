# 🚶 Walkthrough Técnico: Anvic Network Sentinel v2.2.4 (Industrial & Comercial)

> **Perfil:** Staff Engineer & Red Team PhD  
> **Destinatario:** betorock  
> **Versión del Sistema:** v2.2.4 (Producción Comercial & Sistema de Parches)

---

## 🧭 Introducción

Este documento detalla la arquitectura, el flujo de compilación industrial, el sistema de parches diferenciales y la guía de operación para despliegues de **primer uso día cero** y **actualizaciones en caliente** de **Anvic Network Sentinel**.

---

## 🏗️ Arquitectura del Sistema

```
AnvicNetworkMonitorV2.1/
├── main.py                             # Inicializador y despachador de arranque
├── monitor.py                          # Controlador maestro de interfaz, pestañas y eventos
├── build_pipeline.py                   # Pipeline de compilación y firma digital completa
├── build_patch.py                      # Generador industrial de parches diferenciales
├── crear_parche.bat                    # Lanzador interactivo de creación de parches
├── patch_installer.iss                 # Script Inno Setup para actualización diferencial con rollback
├── build_cython.py                     # Transpilador C/C++ Cython para módulos clave
├── AnvicNetworkSentinel.spec           # Especificación PyInstaller con recolección de dependencias
├── installer.iss                       # Script de instalación Inno Setup 7 (LZMA2 Ultra64)
├── seriales_validas.txt                # Registro de seriales criptográficas Pro Perpetua
├── build_profiles/
│   ├── commercial.json                 # Perfil comercial de producción día cero
│   └── demo.json                       # Perfil de demostración limitada
├── core/
│   ├── app.py                          # Lógica de aplicación, persistencia de turnos y estado
│   ├── ping_logic.py                   # Motor ICMP asíncrono y sincrónico thread-safe
│   ├── scraper_ppu.py                  # Scraper PPU (congelado / calibración anti-bloqueo)
│   └── scraper_rut.py                  # Scraper RUT (congelado / formateo automático)
├── licensing/
│   ├── license_service.py              # Servicio de validación y ciclo de vida de licencia
│   ├── license_crypto.py               # Verificación de firma Ed25519 / HMAC
│   ├── license_storage.py              # Almacenamiento seguro en registro Windows / archivo
│   └── machine_fingerprint.py          # Huella digital de hardware inmutable
├── ui/
│   ├── views/                          # Vistas principales
│   ├── components/                     # Componentes visuales (Tarjetas, MapCanvas, Tooltips)
│   └── tabs/                           # Pestañas: Monitoreo, Telemetría, CCTV, OSINT, Admin
└── Output/
    ├── ANS_Patch_V2.2.4.exe            # Instalador ligero de parche firmado (15.16 MB)
    ├── ANS_Patch_V2.2.4_Portable.zip   # Paquete portable con apply_patch y rollback (13.20 MB)
    └── ANS_Setup_V2.2.3.exe            # Instalador completo día cero firmado (92.4 MB)
```

---

## ⚙️ Despliegue de Actualizaciones y Parches

Para generar un nuevo parche diferencial cuando se realicen mejoras menores (sin reinstalación completa y preservando la base de datos de mediciones del cliente):

```powershell
.\monitorEnv\Scripts\python.exe build_patch.py -v 2.2.4 -d "Telemetria adaptativa por turnos y optimizacion multihilo"
```

### Flujo de Protección del Parche:
1. **Pre-flight Tests**: Verificación automatizada con `pytest` (62 pruebas).
2. **PyInstaller Diferencial**: Compila únicamente los bytecodes de la aplicación sin reprocesar dependencias pesadas estáticas.
3. **Backup de Seguridad (Rollback)**: Crea una copia de seguridad en `{app}\backups\` y un script `rollback.bat` antes de sobreescribir el binario en la máquina del cliente.
4. **Cero Afectación**: No toca ni altera `anvic_monitor.db`, `equipos_guardados.json.enc`, `users.json.enc` ni la clave maestra.
5. **Firma Authenticode SHA-256**: Doble firma con timestamp RFC 3161 de DigiCert sobre el ejecutable y el instalador.

---

## 🚀 Guía de Operación (Telemetría Adaptativa y Turnos)

1. **Configuración de Turnos Operacionales:**
   - Ir a la pestaña **Administración** -> Tarjeta *"⏰ Configuración de Turno Operacional"*.
   - Seleccionar `Hora Inicio` (ej. `07:00`) y `Hora Fin` (ej. `18:00`).
   - El sistema soporta turnos normales diurnos y turnos nocturnos que cruzan la medianoche.
   - Pulsar *"💾 Guardar Configuración de Turno"*. La configuración se cifra y se sincroniza en caliente.
2. **Telemetría Dinámica en 4 Modos:**
   - En la pestaña **Telemetría**, alternar con el selector en la cabecera:
     - `Semanal (7D x 24h)`
     - `Semanal (7D x Turno)`
     - `Por Equipo (24h)`
     - `Por Equipo (Turno)`
   - Los KPIs, gauges, gráficos y mapas de calor se recalculan en menos de 15 ms en un hilo secundario sin congelar la interfaz.
3. **Monitoreo en Segundo Monitor:**
   - Pulsar `⧉ Desacoplar` para proyectar el dashboard de telemetría en pantalla secundaria.

---

## 🧪 Validación y Pruebas Automatizadas

```powershell
.\monitorEnv\Scripts\pytest.exe
```

**Resultado:** `62 passed in 7.89s (100% PASS, 0 errors, 0 warnings)`.

