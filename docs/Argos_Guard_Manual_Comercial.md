# Argos Guard (Anvic Network Monitor V2.2)
## Manual de Usuario, Operación Diaria y Valor Comercial

---

### 1. Resumen Ejecutivo
**Argos Guard** es una plataforma de monitoreo de red y seguridad de nivel empresarial, diseñada para operar en centros de control (NOC/SOC). A diferencia de los monitores de red convencionales, Argos Guard unifica en una sola interfaz el monitoreo de infraestructura (ICMP), la vigilancia física (CCTV vía RTSP), herramientas de inteligencia de código abierto (OSINT) y la gestión de operadores bajo un esquema estricto de roles.

El sistema fue diseñado desde cero para garantizar un impacto mínimo en los recursos de hardware, permitiendo monitorear cientos de equipos simultáneamente sin latencia en la interfaz de usuario, gracias a su arquitectura asíncrona de vanguardia.

---

### 2. Uso Diario y Operación (Manual de Usuario)

El diseño de la plataforma se basa en pestañas, permitiendo una transición fluida (incluso por atajos de teclado como `Ctrl+Tab`) para operar con máxima velocidad.

#### 2.1. Inicio de Sesión y Perfiles
Al iniciar, el sistema exige autenticación. Los usuarios se dividen en:
- **Operador:** Tiene acceso al monitoreo en vivo, visualización de cámaras y alertas.
- **Administrador:** Puede añadir/eliminar equipos, modificar cámaras y generar reportes.
- **Super Admin:** Acceso total, incluyendo la gestión de cuentas de usuario, asignación de roles y herramientas OSINT.

#### 2.2. Operación en Vivo (Monitoreo ICMP)
Es el tablero principal del operador de turno.
- **Agregar Equipos:** Ingrese una IP (Ej: `192.168.1.10`) y una Etiqueta (Ej: `Servidor Core`). El sistema automáticamente comenzará a trazar el estado y la latencia.
- **Alertas Visuales y Sonoras:** El sistema cuenta con tarjetas dinámicas (Verde: Online, Rojo: Offline). Las caídas generan una alerta visual inmediata, un sonido característico y una notificación push a un canal de **Telegram** preconfigurado.
- **Uso diario:** El operador mantendrá esta vista abierta. Cualquier desconexión quedará registrada en el Historial para su posterior auditoría.

#### 2.3. Video Vigilancia (CCTV)
Permite centralizar múltiples flujos de cámaras IP/RTSP.
- **Gestión:** Se puede añadir la URL RTSP de una cámara y visualizar el stream de seguridad directamente dentro del programa, sin necesidad de software de terceros.
- **Integración:** Convierte a la estación en un nodo unificado de seguridad física y lógica.

#### 2.4. Servicios OSINT
Para el analista de seguridad avanzada, esta pestaña permite buscar información pública (datos vehiculares y perfiles mediante RUT, según la integración regional). Ayuda a identificar alertas tempranas de incidentes de seguridad que involucren factores humanos o logísticos.

#### 2.5. Administración
El Super Administrador puede crear credenciales, asignar niveles de permisos (roles) y visualizar a todos los operadores registrados. La base de datos de usuarios está **encriptada** para evitar alteraciones locales.

---

### 3. Valores Añadidos y Diferenciadores

1. **Gestión de Carga Inteligente (Batching):** La interfaz gráfica no se congela bajo ninguna circunstancia, garantizando que el operador siempre pueda interactuar, sin importar si hay 5 o 1000 servidores reportando caídas al mismo tiempo.
2. **Navegación Táctica (Hotkeys):** Soporte total para teclado. El operador puede saltar de una pantalla a otra y copiar IPs/Errores usando comandos de teclado estándar (`Ctrl+Tab`, `Ctrl+C`).
3. **Persistencia Total:** Todo evento (caída, recuperación) se guarda de inmediato en una base de datos local SQLite ultrarrápida, ideal para auditorías forenses posteriores.

---

### 4. Valor Comercial del Proyecto

El valor intrínseco de **Argos Guard** en el mercado se fundamenta en su capacidad de sustituir a soluciones de licenciamiento costoso (como PRTG Network Monitor o SolarWinds) para PYMES y entornos corporativos medianos, integrando funciones adicionales que esos softwares no poseen:

- **Ahorro en Licenciamiento:** Solución in-house y "On-Premise" sin pago por cantidad de "sensores".
- **Hardware Liviano (Green IT):** Al usar un motor ICMP Asíncrono puro, la plataforma puede correr en computadoras modestas, Mini-PCs o equipos antiguos del NOC, ahorrando dinero en renovación de hardware para el centro de control.
- **Unificación Híbrida:** Normalmente, una empresa paga un software para vigilar la red, y otro software (VMS) para sus cámaras. **Argos Guard unifica ambos**, reduciendo la curva de aprendizaje de los operadores y disminuyendo las pantallas necesarias en el Centro de Monitoreo.
- **Estabilidad Certificada (E2E):** El código cuenta con una suite de pruebas de caja negra automatizada, lo que garantiza comercialmente que cada compilación funciona sin errores antes de entregarse al cliente final.
