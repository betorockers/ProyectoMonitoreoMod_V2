# Requerimientos del Sistema
## Anvic Network Sentinel v2.2

Este documento define los requisitos recomendados para instalar y operar **Anvic Network Sentinel** con estabilidad, buen rendimiento visual y capacidad real de monitoreo, diagnóstico y supervisión visual.

---

## 1. Alcance de operación esperado

Anvic Network Sentinel puede ejecutarse en estaciones de trabajo, mini PCs, notebooks técnicas y puestos de monitoreo dedicados. Su carga depende de cinco factores principales:

1. Cantidad de equipos monitoreados en paralelo.
2. Frecuencia de chequeo de red.
3. Uso de módulos avanzados como `HTTP/HTTPS`, `puertos`, `SNMP` y `SSH`.
4. Generación de reportes PDF con gráficos históricos.
5. Uso de `Supervisión Visual` con snapshots o streams RTSP.

---

## 2. Sistemas operativos compatibles

### Soportado oficialmente

- Windows 10 Pro / Enterprise 64 bits
- Windows 11 Pro / Enterprise 64 bits

### Compatible con limitaciones

- Windows 10 Home / Windows 11 Home 64 bits  
  Puede funcionar correctamente, pero no es el escenario ideal para despliegues corporativos.

### No recomendado para esta release

- Windows de 32 bits
- Windows 7 / 8 / 8.1
- Linux o Raspberry Pi en esta rama de distribución

Nota: aunque el código podría adaptarse a otros entornos, la distribución actual, el instalador y el flujo de soporte están pensados para **Windows 64 bits**.

---

## 3. Perfiles de hardware recomendados

## Perfil 1: Operación básica
Pensado para pruebas, instalaciones pequeñas o estaciones con baja carga.

- CPU: 2 núcleos físicos a 2.0 GHz o superior
- RAM: 4 GB
- Almacenamiento libre: 2 GB
- Red: Ethernet 100 Mbps o Wi-Fi estable
- Pantalla: 1366x768 o superior

Uso esperado:
- hasta 10 equipos monitoreados
- monitoreo ICMP
- historial básico
- reportes ocasionales
- snapshots simples de cámara

## Perfil 2: Operación recomendada
Pensado para la mayoría de instalaciones reales y uso diario profesional.

- CPU: 4 núcleos a 2.4 GHz o superior
- RAM: 8 GB
- Almacenamiento libre: 5 GB SSD recomendado
- Red: Ethernet 1 Gbps recomendada
- Pantalla: 1920x1080

Uso esperado:
- 10 a 40 equipos monitoreados
- diagnósticos de red frecuentes
- uso de `HTTP/HTTPS`, `Puertos`, `SNMP` y `SSH`
- generación de reportes PDF con gráficos grandes
- perfiles de cámara y snapshots operativos

## Perfil 3: Centro de monitoreo / uso intensivo
Pensado para supervisión continua, operación visual y múltiples chequeos concurrentes.

- CPU: Intel Core i7 / Ryzen 7 o superior
- RAM: 16 GB o más
- Almacenamiento libre: 10 GB SSD
- Red: Ethernet 1 Gbps
- Pantalla: Full HD o doble monitor
- GPU: integrada moderna o dedicada básica, suficiente para escritorio fluido

Uso esperado:
- 40 a 100 equipos monitoreados
- múltiples chequeos activos
- reportes frecuentes
- uso intensivo de `Supervisión Visual`
- mosaico de cámaras y streams simultáneos controlados

---

## 4. Requisitos específicos para Supervisión Visual

El módulo de cámaras depende fuertemente del hardware anfitrión.

### Snapshot HTTP

- Bajo consumo
- Adecuado para equipos modestos
- Permite confirmación visual rápida

### RTSP en vivo

- Requiere mayor CPU, RAM y red
- Depende de la calidad del stream, codec y resolución
- Debe operarse con límite de streams simultáneos configurado desde administración

### Recomendación práctica

- 1 a 2 streams simultáneos: equipos de perfil recomendado pueden operar bien
- 3 a 6 streams simultáneos: usar perfil de centro de monitoreo
- más de 6 streams: evaluar muy bien el host, la red y la resolución de cada cámara antes de considerarlo productivo

---

## 5. Requisitos de red

- Conectividad IP estable entre el host Sentinel y los equipos monitoreados
- Resolución DNS funcional para pruebas de `lookup` y monitoreo web
- ICMP permitido cuando se use monitoreo por ping
- Puertos de servicio abiertos según el tipo de activo monitoreado
- Para `SNMP`: comunidad y acceso habilitados en el equipo remoto
- Para `SSH`: credenciales válidas y acceso autorizado
- Para `HTTP/HTTPS`: endpoints accesibles desde el host Sentinel
- Para `RTSP`: ruta de stream válida y conectividad hacia el puerto correspondiente

---

## 6. Requisitos funcionales por módulo

## Monitoreo operativo

- CPU y RAM bajos
- Puede operar bien en hardware modesto

## Historial y reportes

- Requiere más memoria y almacenamiento por el crecimiento del historial
- Recomendado SSD para mejor respuesta

## Centro de Soporte

- Depende más de conectividad y privilegios que de hardware
- Requiere acceso de red real a los activos

## Supervisión Visual

- Módulo más exigente de la plataforma
- La experiencia depende del número de cámaras, refresco y streams activos

---

## 7. Requisitos de software

- Python no es necesario para la versión instalada por setup
- Microsoft Visual C++ Redistributable moderno recomendado
- Windows Defender o antivirus corporativo con política que permita la instalación firmada o autorizada
- Acceso al certificado raíz correspondiente si la organización usa inspección TLS

---

## 8. Privilegios y permisos

La aplicación fue diseñada para ejecutarse con el menor privilegio posible, pero algunas funciones requieren permisos o contexto adecuado.

### Funciona normalmente sin privilegios elevados para:

- monitoreo general
- historial
- reportes
- HTTP/HTTPS
- SNMP
- SSH
- snapshots y visualización

### Puede requerir condiciones especiales para:

- ciertas consultas de red locales
- lectura avanzada del host
- operaciones de recuperación local
- interacción con servicios del sistema

Recomendación:
- usar una cuenta de operador o administrador técnico autorizada
- no ejecutar como administrador salvo necesidad operativa real

---

## 9. Requisitos para licenciamiento

- El instalador solicita serial de activación
- La aplicación valida la licencia en el primer arranque
- La licencia se vincula al equipo anfitrión
- Las licencias anuales requieren fecha vigente
- Las licencias trial tienen vigencia limitada de 30 días

---

## 10. Recomendación por tipo de despliegue

## Notebook técnico

- válido para soporte en terreno
- ideal con 8 GB RAM y SSD
- recomendado para diagnósticos y operación puntual

## Mini PC en instalación

- válido para monitoreo local estable
- recomendado cuando la instalación requiere puesto dedicado
- ideal con Ethernet y UPS

## Estación de monitoreo en oficina o central

- escenario ideal para la versión `Advanced` o `Pro`
- recomendado para múltiples instalaciones, reportes y operación visual

---

## 11. Conclusión operativa

Anvic Network Sentinel puede funcionar en hardware modesto para monitoreo básico, pero para aprovechar bien la versión `Advanced` y especialmente la `Pro`, se recomienda una estación Windows 64 bits con:

- CPU de 4 núcleos o más
- 8 GB RAM mínimo
- SSD
- red estable
- resolución Full HD

Para operación con cámaras, múltiples chequeos y uso continuo, la recomendación sube a:

- 16 GB RAM
- CPU de gama media-alta
- Ethernet 1 Gbps
- configuración explícita del límite de streams simultáneos

---

**Producto:** Anvic Network Sentinel  
**Versión de referencia:** 2.2  
**Documento actualizado:** Marzo 2026
