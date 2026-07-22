# Reestructuración Arquitectónica: Motor de Telemetría (Daemon)

Hemos completado el desacoplamiento del motor de monitoreo de la interfaz de usuario, migrándolo hacia un **Demonio de Fondo (Background Daemon)**.

## ¿Qué ha cambiado?
1. **Precisión Militar Autónoma**:
   - Todo el código que enviaba pings (TCP/ICMP) fue movido de la vista de Django (`views.py`) hacia un nuevo script dedicado: `apps/monitoring/daemon.py`.
   - Este demonio es un hilo (Thread) que corre un ciclo infinito (Loop) en segundo plano con una cadencia ultrarrápida de 2 segundos de forma ininterrumpida, sin importar si la interfaz está abierta, cerrada o minimizada.

2. **Frontend Ultra Ligero**:
   - Eliminamos todo el código AlpineJS que controlaba el temporizador en la pestaña "Monitoreo Activo".
   - Eliminamos la caja de texto "Intervalo Ping (s)" del panel lateral, dado que ahora el Backend asume el control absoluto del timing.
   - El contenedor visual de tarjetas de equipos simplemente interroga pasivamente a la base de datos (con tecnología nativa HTMX `every 2s`) para repintar las tarjetas con los datos más recientes arrojados por el Demonio.
   - Dado que ya no ejecuta los ping directamente, la interfaz gráfica será significativamente más fluida.

3. **Sistema de Alertas (Cola en Memoria)**:
   - Dado que el demonio corre en paralelo, se implementó una cola en memoria RAM (`queue.Queue`) que atrapa los eventos de "Caída" y "Levantamiento" (Toasts) y se los pasa discretamente al Frontend en el próximo refresco, manteniendo vivas las notificaciones visuales emergentes.

## Resultados Esperados
Si vuelves a abrir la aplicación desde cero y colocas a prueba las desconexiones junto a la versión antigua de tu aplicación, **ambas deberían ahora registrar la caída simultáneamente**, ya que el motor de fondo de nuestra V4 ahora sí escanea la red implacablemente y sin depender de ventanas activas del navegador.
