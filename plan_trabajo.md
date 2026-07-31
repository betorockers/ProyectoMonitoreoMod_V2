# Plan de Trabajo
## Anvic Network Sentinel v2.2.1

Este documento resume el plan de trabajo vigente del proyecto, diferenciando lo ya ejecutado, lo que queda recomendado antes de una liberación formal y las líneas futuras de evolución.

---

## 1. Objetivo general

Consolidar Anvic Network Sentinel como una plataforma estable de monitoreo técnico y visual para uso interno de ANVIC y como base de una futura oferta de servicio comercializable.

---

## 2. Trabajo ya ejecutado

### Producto e identidad

- consolidación de marca `Anvic Network Sentinel`
- alineación visual de app, iconos, ejecutable e instalador
- textos de producto y documentación institucional

### Plataforma funcional

- monitoreo operativo de equipos
- historial operacional
- reportes PDF
- centro de soporte
- diagnósticos de red
- HTTP/HTTPS
- puertos
- SNMP
- SSH
- supervisión visual
- perfiles de cámara
- video en vivo y mosaico básico controlado
- notificaciones Telegram configurables por instalación

### Seguridad

- endurecimiento de build
- `UPX` desactivado
- TLS configurable con postura estricta
- geolocalización externa opcional
- validación SSH de host key
- saneamiento de secretos
- consolidación de almacenamiento seguro
- licenciamiento firmado offline
- Telegram sin credenciales embebidas por defecto

### Entrega y comercialización

- documentos gerenciales
- documentos técnico-comerciales
- matrices de licenciamiento
- requerimientos del sistema
- manual de usuario
- lotes de licencias emitidos
- documentación alineada con el módulo Telegram administrable

---

## 3. Trabajo recomendado para cierre de liberación

Estas tareas ya no son de desarrollo base, sino de aseguramiento de release:

### Prioridad alta

- smoke test final del instalador
- smoke test final del flujo de licencia
- prueba de apertura y operación del ejecutable instalado
- validación de desinstalación y persistencia mínima de licencia

### Prioridad alta

- firma digital del ejecutable
- firma digital del instalador
- prueba en Windows limpio con Defender activo

### Prioridad media

- validación operativa del módulo RTSP con fuente real o laboratorio estable
- empaquetado de entrega formal para uso interno o presentación a ANVIC

---

## 4. Trabajo futuro sugerido

### Línea 1: robustecimiento comercial

- backend de activación y revocación
- evaluación de backend `Supabase` como opción preferente y `Firebase` como alternativa
- control centralizado de licencias
- expiración y renovación asistida
- telemetry liviana de estado de licencia

### Línea 2: producto operativo

- mayor madurez del mosaico de cámaras
- perfiles por fabricante
- mejoras de detección visual y congelamiento de imagen
- más presets por tipo de instalación

### Línea 3: hardening avanzado

- firma de código
- anti-tamper adicional
- revisión defensiva de logs y almacenamiento
- eventuales medidas de ofuscación o compilación en rama separada

### Línea 4: exploración técnica futura

- evaluación de Nuitka en rama independiente
- comparación de tamaño, compatibilidad y superficie de exposición

---

## 5. Estado del plan

### Completado

- construcción del núcleo funcional actual
- construcción del módulo visual
- endurecimiento principal de seguridad
- instalación moderna
- licenciamiento operativo
- documentación ejecutiva, técnica y comercial

### En cierre

- smoke test final manual
- firma digital
- validación final de release

### Futuro

- backend de activación
- escalamiento comercial
- nuevas integraciones avanzadas

---

## 6. Criterio de término para la v2.2

La versión `2.2.1` puede declararse cerrada cuando se cumplan estos cuatro puntos:

1. instalador validado manualmente
2. licencia validada en instalación nueva
3. apertura correcta del ejecutable instalado
4. documentación final alineada y resguardada

---

**Producto:** Anvic Network Sentinel  
**Versión:** 2.2.1  
**Estado del plan:** Cierre de release
