# Argos Guard (Anvic Network Monitor V2.2)
## Documentación Técnica y Arquitectura del Sistema

Esta documentación está orientada a desarrolladores, ingenieros de sistemas e integradores que deseen comprender, modificar o escalar el proyecto **Argos Guard**.

---

### 1. Stack Tecnológico
- **Lenguaje Principal:** Python 3.11+
- **Interfaz Gráfica (GUI):** `CustomTkinter` (UI Moderna, soporte para Dark Mode nativo).
- **Base de Datos:** `SQLite` (Modo WAL habilitado para concurrencia).
- **Concurrencia y Red:** `asyncio` nativo combinado con `icmplib` (sin privilegios root) para networking asíncrono.
- **Testing:** `pytest` (Caja negra / Automatización UI).

---

### 2. Arquitectura de Módulos (Core)

El proyecto utiliza un diseño modular acoplado a un bucle principal de interfaz gráfica (Mainloop).

#### 2.1. `monitor.py` (Controlador Principal)
Es el punto de entrada y gestor del ciclo de vida de la UI.
- **Función:** Instancia `App(customtkinter.CTk)` y carga las pestañas.
- **Motor UI (Queue):** Implementa un patrón `queue.Queue`. En lugar de que los hilos secundarios modifiquen la UI (lo cual rompe Tkinter o genera "lag"), los hilos envían diccionarios a la cola. El método `process_ui_queue()` procesa hasta 50 eventos cada 100ms utilizando `after()`, manteniendo la UI siempre a 60 FPS.
- **Cómo modificar:** Si agregas una nueva métrica que impacte la interfaz, envía el payload a `self.ui_queue.put(data)` y crea un manejador en `process_ui_queue()`.

#### 2.2. `core/ping_logic.py` (Motor Asíncrono ICMP)
Reemplaza al antiguo sistema Thread-por-IP.
- **Función:** Levanta un bucle asíncrono (`asyncio.new_event_loop()`) en un único hilo en segundo plano (Daemon). 
- **Mecánica:** Utiliza `async_multiping` de la librería `icmplib` para golpear hasta 250 IPs de manera concurrente usando sockets raw. Consume virtualmente 0% de CPU.
- **Cómo modificar:** Las reglas de tolerancia de latencia y tiempos de `timeout` se encuentran en el bloque de inicialización de `icmplib`.

#### 2.3. `core/process_manager.py` (Manejo de Ciclo de Vida y Memoria)
- **Función:** Detecta y limpia procesos huérfanos generados por librerías subyacentes o de WebScraping (Ej: instancias de `chromedriver` en OSINT o `ping.exe` residuales).
- **Mecánica:** Se suscribe mediante `atexit.register()`. Cuando la app muere (incluso por un crasheo), asegura liberar la RAM del Sistema Operativo.

#### 2.4. `database/database_manager.py` y `metrics_manager.py` (Persistencia)
- **Función:** Gestiona la capa de datos. Almacena las mediciones de latencia, estados históricos e inventario de red.
- **Optimización WAL:** Emplea `PRAGMA journal_mode=WAL;` y `PRAGMA synchronous=NORMAL;`. Esto permite que el hilo secundario (Pings) inserte mediciones mientras el Hilo Principal (UI) lee gráficos simultáneamente, eliminando el clásico error `sqlite3.OperationalError: database is locked`.

#### 2.5. Pestañas de Interfaz (`ui/tabs/`)
Se componen de varios submódulos para no saturar `monitor.py`:
- `admin_tab.py`: Control de usuarios (con escritura cifrada a `users.json.enc`).
- `video_vigilancia_tab.py`: Utiliza librerías de streaming embebidas para cargar frames RTSP o HTTP.
- `osint_tab.py`: Scripts de Scraping web con perfiles aleatorios (`FakeUserAgent`) para extraer datos abiertos.

---

### 3. Guía de Modificación e Implementación

#### 3.1. Añadir una Nueva Pestaña (Tab)
1. Crea un nuevo archivo en `ui/tabs/` (Ej: `ui/tabs/reportes_tab.py`).
2. Diseña la clase heredando o recibiendo el master frame:
   ```python
   class ReportesTab:
       def __init__(self, app_controller, tab_frame):
           self.app = app_controller
           self.frame = tab_frame
           # Renderizar UI aquí
   ```
3. En `monitor.py`, dentro de `setup_main_ui()`, añade:
   ```python
   self.tab_reportes = self.tabview.add("Reportes Avanzados")
   self.reportes_controller = ReportesTab(self, self.tab_reportes)
   ```

#### 3.2. Implementar una Nueva Métrica en Base de Datos
Si deseas registrar, por ejemplo, los "Paquetes Perdidos" además de la latencia:
1. Ve a `database/database_manager.py` -> `init_db()`.
2. Añade la nueva columna al comando `CREATE TABLE IF NOT EXISTS metrics`.
3. Actualiza la consulta SQL de inserción en `metrics_manager.py` (`agregar_medicion()`) para aceptar y grabar este nuevo argumento.
4. En `core/ping_logic.py`, lee la pérdida de paquetes de `host.packet_loss` (provisto por `icmplib`) y envíala en el Queue hacia la UI/BD.

---

### 4. Flujo E2E (Pruebas Automatizadas)
El sistema incluye integración continua manual usando **PyTest**.
- **Archivo:** `tests/test_e2e_gui.py`
- **Funcionamiento:** Instancia la clase `App` pero bypassea el bucle `mainloop()`. Simula la interacción inyectando textos en los `CTkEntry` e invocando los botones (`btn.invoke()`), para luego leer el estado interno.
- **Para probar tu código modificado:** Ejecuta siempre `python -m pytest tests/test_e2e_gui.py -v` antes de hacer un commit o compilación. Si falla un test, tu cambio rompió la interfaz.
