# Fases del Proyecto
## Anvic Network Sentinel

Este documento organiza el proyecto por fases de evolución real, desde su origen como monitor de red hasta su estado actual como plataforma técnica y visual en versión `2.2.1`.

---

## Fase 0: Origen operativo

### Objetivo
Resolver una necesidad concreta de monitoreo de equipos conectados dentro de instalaciones reales.

### Resultado
- monitoreo básico de IPs
- visibilidad de estado online/offline
- primera utilidad operativa en terreno

---

## Fase 1: Consolidación de monitoreo

### Objetivo
Pasar de un monitor simple a una herramienta usable de operación diaria.

### Resultado
- operación en vivo
- historial operacional
- métricas de latencia
- eventos y disponibilidad
- reportes iniciales

---

## Fase 2: Expansión técnica del diagnóstico

### Objetivo
Convertir la app en una herramienta de soporte técnico real, no solo de disponibilidad.

### Resultado
- pestaña de diagnóstico
- `ping`, `tracert`, `lookup`
- información del host local
- recuperación técnica local
- ARP y sesiones de red
- mejora del enfoque de soporte

---

## Fase 3: Expansión por protocolos

### Objetivo
Aumentar el valor técnico del producto sobre infraestructura y servicios reales.

### Resultado
- `HTTP/HTTPS`
- escaneo controlado de puertos
- `SNMP` básico
- `SSH` de consulta
- mayor profundidad de validación por tipo de equipo

---

## Fase 4: Supervisión visual

### Objetivo
Agregar capacidad visual a la plataforma para entornos de seguridad y CCTV.

### Resultado
- perfiles de cámara
- pruebas snapshot
- pruebas RTSP
- vista `Video en Vivo`
- base de mosaico multi-cámara
- control de streams simultáneos

---

## Fase 5: Profesionalización del producto

### Objetivo
Alinear identidad, estructura y presentación del software a un estándar comercial y corporativo.

### Resultado
- branding completo de Anvic Network Sentinel
- iconografía institucional
- nombres comerciales de módulos y tabs
- reportes PDF más formales
- documentación ejecutiva, comercial y técnica

---

## Fase 6: Hardening y release

### Objetivo
Preparar el software para una entrega más seria en términos de seguridad, instalación y reputación técnica.

### Resultado
- modernización de `spec`
- modernización de `installer.iss`
- instalador en español
- `UPX` desactivado
- limpieza de dependencias de release
- build recompilado desde entorno correcto

---

## Fase 7: Licenciamiento profesional

### Objetivo
Dar al producto una base comercial real y controlada.

### Resultado
- licencias firmadas offline
- serial en wizard
- activación en primer arranque
- soporte para `TRIAL`, `ANNUAL` y `PERPETUAL`
- soporte para `STANDARD`, `ADVANCED` y `PRO`
- lotes emitidos y resguardados

---

## Fase 8: Ciberseguridad aplicada

### Objetivo
Reducir exposición operacional y elevar la postura defensiva del producto.

### Resultado
- saneamiento de secretos
- eliminación de hardcodes críticos
- TLS configurable con enfoque estricto
- geolocalización externa opcional
- validación SSH con host key y TOFU opcional
- mayor coherencia entre la rama activa y la modular
- Telegram sin tokens ni chat IDs hardcodeados

---

## Fase 9: Alertamiento operativo configurable

### Objetivo
Incorporar alertamiento opcional de Telegram con control total desde administración y sin exponer credenciales en el código.

### Resultado
- módulo de configuración Telegram en `Administración`
- ingreso manual de `token` y `chat_id` por parte del administrador
- configuración de nombre de instalación y título base de mensajes
- alertas por caída, recuperación y gravedad
- alerta crítica al superar 5 minutos continuos desconectado
- identificación explícita de la instalación en cada mensaje enviado

---

## Fase 10: Cierre de la v2.2.1

### Objetivo
Dejar una versión técnicamente sólida, documentada y lista para validación final.

### Resultado actual
- ejecutable final compilado
- instalador final compilado
- licencias emitidas
- documentación actualizada
- suite de pruebas estable

Pendiente de esta fase:
- smoke final manual
- firma digital
- validación final de instalación y desinstalación

---

## Fase 11: Evolución futura

### Líneas posibles

- backend de activación centralizado
- mejoras RTSP y mosaico
- más perfiles de cámara
- firma de código y reputación binaria
- evaluación futura de Nuitka en rama separada

---

## Conclusión

Anvic Network Sentinel pasó de ser una herramienta nacida desde una necesidad de soporte a una plataforma con estructura suficiente para operación real, proyección comercial y crecimiento interno dentro de ANVIC.

---

**Producto:** Anvic Network Sentinel  
**Versión de referencia:** 2.2.1  
**Estado:** Fase de cierre técnico y validación final
