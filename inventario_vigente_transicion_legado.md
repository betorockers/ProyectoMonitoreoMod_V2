# Inventario Técnico: Vigente vs Transición vs Legado

## Propósito

Este documento separa el proyecto en cuatro zonas:

- **Vigente:** lo que hoy gobierna la aplicación real
- **Transición:** lo nuevo que existe, pero aún no manda
- **Legado:** lo histórico o duplicado que no debería seguir siendo la referencia
- **Artefactos/Operación:** archivos útiles para correr o distribuir, pero que no son núcleo del código

La meta es evitar tocar el proyecto a ciegas.

---

## Conclusión Ejecutiva

### Base oficial temporal recomendada

Si vamos a ordenar el software sin romperlo, la base oficial temporal debe asumirse así:

- `main.py`
- `monitor.py`
- `ping_logic.py`
- `metrics_manager.py`
- `auth_manager.py`
- `key_manager.py`
- `secure_config_manager.py`
- `network_tools_logic.py`
- `config/branding.py`
- activos reales de `assets/`

### Motivo

Porque esa es la cadena que hoy realmente arranca y controla la aplicación.

La arquitectura modular nueva todavía **no** es la base activa del producto, aunque sí representa la mejor dirección futura.

---

## 1. Zona Vigente

## Entry point real

### `main.py`

Estado:

- **Vigente**

Razón:

- arranca la aplicación real con `from monitor import App`

Conclusión:

- cualquier cambio que no considere `monitor.py` hoy no está atacando el corazón real del sistema

## Núcleo actual real

### `monitor.py`

Estado:

- **Vigente**

Razón:

- contiene la `App` real
- contiene login, setup, monitoreo, historial, diagnósticos, usuarios, scheduler, reportes y gran parte de la orquestación

Lectura:

- hoy es el monolito operativo principal

### `ping_logic.py`

Estado:

- **Vigente**

Razón:

- es importado directamente por `monitor.py`

### `metrics_manager.py`

Estado:

- **Vigente**

Razón:

- es importado directamente por `monitor.py`
- alimenta SQLite para la rama activa

### `auth_manager.py`

Estado:

- **Vigente**

Razón:

- es importado directamente por `monitor.py`
- gobierna autenticación en la rama activa

Comentario:

- esta versión usa `bcrypt` y persistencia cifrada con apoyo de `SecureConfigManager`

### `key_manager.py`

Estado:

- **Vigente**

Razón:

- es usado por `monitor.py` para cargar/generar la clave maestra

### `secure_config_manager.py`

Estado:

- **Vigente**

Razón:

- la rama activa lo usa para cifrar/descifrar configuración y usuarios

### `network_tools_logic.py`

Estado:

- **Vigente**

Razón:

- `monitor.py` lo usa para validación y ejecución segura de comandos

## Configuración/branding efectivamente consumidos

### `config/branding.py`

Estado:

- **Vigente pero inconsistente**

Razón:

- `monitor.py` importa `APP_NAME`, `VERSION`, `AUTHOR`, `LOGO_FILE`, `ICON_FILE`

Problemas observados:

- el archivo dice “Argos Guard” en comentarios
- `APP_NAME` está en `Anvic Network Monitor`
- el tema dice “Sentinel”
- `ICON_FILE = "sentinel_icon.ico"` pero ese archivo no existe en `assets/img`
- `LOGO_FILE = "logoAnvic.png"` sí existe y por ahora es el branding más alineado a Anvic

Conclusión:

- esta pieza es vigente, pero necesita ser corregida y consolidada

## Activos visuales realmente disponibles

### `assets/img/logoAnvic.png`

Estado:

- **Vigente**

Razón:

- coincide con `LOGO_FILE`
- responde a la identidad Anvic

### `assets/img/icono_argos.ico`

Estado:

- **Vigente de facto / inconsistente con configuración**

Razón:

- el `.spec` y partes de UI modular lo usan
- existe físicamente
- pero no coincide con `ICON_FILE` en `config/branding.py`

### `assets/img/LogoArgosGuard.png`

Estado:

- **Transición o branding alterno no oficial para esta versión**

Razón:

- existe y es usado en documentación o ramas parciales
- no se alinea con la decisión actual de mantener Anvic Network Sentinel

---

## 2. Zona de Transición

Esta zona contiene la refactorización modular nueva.

## Carpetas

### `core/`

Estado:

- **Transición**

Razón:

- contiene una `App` nueva más modular
- no es la que arranca `main.py`

Lectura:

- buena dirección de arquitectura
- no es todavía la fuente oficial del comportamiento real

### `ui/`

Estado:

- **Transición**

Razón:

- contiene tabs, ventanas y componentes ya desacoplados
- no gobierna la app real porque la app activa sigue centralizada en `monitor.py`

### `services/`

Estado:

- **Transición**

Razón:

- encapsula mejor Telegram y herramientas de red
- aún no domina el runtime real

### `database/`

Estado:

- **Transición**

Razón:

- introduce una capa más limpia para SQLite
- no es la base usada por `monitor.py`

### `auth/`

Estado:

- **Transición**

Razón:

- contiene una nueva capa de autenticación separada
- pero no es la autenticación que hoy usa la app real

Comentario importante:

- esta rama nueva se ve más ordenada, pero en seguridad parece más débil que la rama vigente

## Archivos representativos de transición

### `core/app.py`

Estado:

- **Transición**

Comentario:

- probablemente debe convertirse en la base futura
- todavía no tiene autoridad real mientras `main.py` siga entrando por `monitor.py`

### `ui/windows/login_window.py`

Estado:

- **Transición con inconsistencias**

Problemas:

- usa textos de Argos Guard
- referencia `logoargosguard.png`, archivo que no existe con ese nombre exacto en `assets/img`

### `services/network_tools.py`

Estado:

- **Transición valiosa**

Comentario:

- es una mejor capa que `network_tools_logic.py` desde el punto de vista de separación de responsabilidades

---

## 3. Zona de Legado

## Carpeta `legacy/`

Estado:

- **Legado claro**

Razón:

- contiene copias históricas o archivadas de módulos ya presentes en el proyecto principal

Regla recomendada:

- no usarla como referencia funcional para cambios nuevos
- conservarla solo hasta terminar limpieza y migración

## Documentación de branding viejo o mezcla de producto

Archivos como:

- `ESTRATEGIA_PRODUCTO_ARGOS_GUARD.md`
- partes importantes de `docs/`
- `documentacion.md`
- `docs/documentacion.md`
- `docs/guia_usuario.md`

Estado:

- **Legado conceptual o transición documental**

Razón:

- describen el producto como Argos Guard o mezclan Sentinel/Argos/Monitor

## Lanzadores alternos

### `launch_argos_guard.bat`

Estado:

- **Legado o transición**

Razón:

- apunta a la misma app, pero con naming distinto del que ahora queremos conservar

### `Anvic_Sentinel_V2.bat`

Estado:

- **Vigente como soporte operativo**

Razón:

- el nombre coincide mejor con la identidad deseada de esta versión

---

## 4. Artefactos y Operación

Estos archivos no son el núcleo del software, pero sí forman parte del ecosistema de uso.

## Build y distribución

### `ArgosGuard.spec`

Estado:

- **Artefacto de distribución vigente pero con naming incorrecto**

Razón:

- empaqueta la app real desde `main.py`
- pero genera producto `ArgosGuard`

### `installer.iss`

Estado:

- **Artefacto crítico en mal estado**

Razón:

- mezcla branding Sentinel y Argos Guard
- tiene conflicto de merge sin resolver

Conclusión:

- no debe tocarse a ciegas
- necesita saneamiento temprano porque afecta releases

## Datos operativos

Archivos como:

- `anvic_monitor.db`
- `argos_guard.db`
- `users.json.enc`
- `equipos_guardados.json.enc.corrupt.*`
- `users.json.enc.corrupt.*`
- `historial_log.txt`
- `Reporte_Sentinel_*.pdf`
- `*.bak`
- `*.key`

Estado:

- **Artefactos operativos**

Razón:

- forman parte de uso, pruebas o residuos de operación
- no son módulos de negocio

Comentario:

- no conviene tratarlos como código
- tampoco conviene borrarlos sin estrategia de migración y respaldo

## Carpetas no núcleo

### `build/`, `dist/`, `Output/`

Estado:

- **Artefactos de distribución**

### `monitorEnv/`

Estado:

- **Infraestructura local de desarrollo/ejecución**

### `backups/`

Estado:

- **Operación**

---

## 5. Mapa de Decisión Recomendado

## Qué tratar como oficial desde ya

- nombre operativo de esta versión: **Anvic Network Sentinel**
- cadena de ejecución actual: `main.py -> monitor.py`
- rama activa de seguridad: la de `auth_manager.py` + `secure_config_manager.py` + `key_manager.py`
- branding base a preservar: línea Anvic

## Qué tratar como objetivo futuro, no presente

- `core/`
- `ui/`
- `services/`
- `database/`
- `auth/`

Es decir:

- no descartarlos
- no asumir que ya mandan

## Qué tratar como histórico o referencia secundaria

- `legacy/`
- documentación fuertemente Argos Guard
- lanzadores y empaquetados con naming antiguo

---

## 6. Recomendación de Arranque para el Ordenamiento Real

Antes de refactor grande, el siguiente orden lógico sería:

1. fijar branding oficial de esta versión a **Anvic Network Sentinel**
2. alinear `config/branding.py` con assets reales
3. declarar a `monitor.py` como núcleo temporal oficial mientras ordenamos
4. inventariar duplicados funcionales módulo por módulo
5. decidir luego qué piezas modulares heredan el comportamiento vigente sin perder seguridad

---

## Cierre

Hoy el proyecto no está “sin forma”.
Sí tiene forma, pero esa forma real no coincide todavía con la arquitectura que parece querer tener.

La verdad práctica es esta:

- la app real vive en el monolito
- la arquitectura modular vive como transición
- el branding está mezclado
- la limpieza debe partir desde la realidad, no desde la intención

Esa es la base correcta para empezar el viaje sin romper lo que ya sirve.
