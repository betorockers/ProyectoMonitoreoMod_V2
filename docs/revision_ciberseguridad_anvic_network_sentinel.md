# Revision de Ciberseguridad - Anvic Network Sentinel

Fecha: 2026-03-20

## 1. Resumen ejecutivo

Anvic Network Sentinel `v2.2.1` presenta una postura de seguridad claramente mas madura que en fases previas. La aplicacion ya no depende de secretos embebidos para Telegram, opera con licenciamiento firmado offline, mantiene controles sobre TLS y SSH, y deja la configuracion sensible bajo un esquema mas seguro.

La lectura actual es:

- apta para un release comercial controlado
- mejor protegida frente a manipulacion casual y uso no autorizado
- todavia recomendable de complementar con firma digital y pruebas finales de entorno limpio

---

## 2. Fortalezas vigentes

### 2.1 Proteccion local de configuracion

- uso de clave maestra protegida con DPAPI en Windows
- configuracion principal cifrada mediante `SecureConfigManager`
- persistencia de licencia protegida y ligada al equipo

### 2.2 Licenciamiento comercial

- licencias firmadas con validacion criptografica
- soporte para `TRIAL`, `ANNUAL` y `PERPETUAL`
- soporte para `STANDARD`, `ADVANCED` y `PRO`
- validacion al arranque y durante el flujo de activacion

### 2.3 Superficie de build

- build PyInstaller sin `UPX`
- instalador moderno orientado a perfil de usuario
- empaquetado Tcl/Tk estabilizado

### 2.4 Red y protocolos

- politica TLS configurable con enfoque estricto
- geolocalizacion externa opcional
- politica SSH con validacion de host key y modo TOFU opcional

### 2.5 Telegram

- sin `token` ni `chat_id` hardcodeados en la version comercial
- activacion opcional solo desde `Administracion`
- configuracion por instalacion con nombre identificador del origen

---

## 3. Hallazgos corregidos en la ronda final

### R-01. Credenciales Telegram embebidas

Estado:

- corregido
- defaults vacios en configuracion
- sin credenciales precargadas en la ruta comercial

### R-02. Alertamiento Telegram administrable

Estado:

- corregido e integrado
- alta manual de `token`, `chat_id`, nombre de instalacion y titulo base
- alertas por caida, recuperacion y gravedad tras 5 minutos desconectado

### R-03. Postura de red configurable

Estado:

- corregido e integrado
- TLS y geolocalizacion externa ahora son politicas visibles de administracion
- SSH ya no depende de aceptacion ciega de host key como ruta recomendada

---

## 4. Riesgos remanentes

Aunque la postura general es buena, todavia conviene considerar estos puntos:

- firma digital pendiente del ejecutable e instalador
- dependencia de buenas practicas locales del administrador al cargar secretos operativos
- necesidad de pruebas manuales finales de instalacion, activacion y desinstalacion
- la proteccion antiingenieria inversa sigue siendo de barrera alta, no absoluta

---

## 5. Recomendaciones

### Prioridad alta

- firmar digitalmente ejecutable e instalador
- validar release en Windows limpio con Defender activo
- respaldar y custodiar fuera del repo las claves privadas de emision

### Prioridad media

- evaluar backend futuro de activacion y revocacion
- ampliar controles de auditoria sobre configuracion sensible
- endurecer aun mas reputacion binaria para despliegues externos

---

## 6. Conclusión

La `v2.2.1` ya no presenta la situacion de riesgo que implicaba mantener Telegram con secretos embebidos o defaults operativos inseguros. El producto queda mucho mejor posicionado para una adopcion interna seria y una futura maduracion comercial controlada.

---

**Producto:** Anvic Network Sentinel  
**Version:** 2.2.1  
**Estado:** Hardening principal completado
