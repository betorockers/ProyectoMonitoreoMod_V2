# Mejoras Futuras
## Anvic Network Sentinel

Este documento resume lineas de evolucion recomendadas para futuras iteraciones del producto.

---

## 1. Backend de activacion y licencias

### Objetivo

Evitar reutilizacion de una misma serial en distintos equipos y dar mayor control comercial a ANVIC.

### Alcance esperado

- registro centralizado de activaciones
- asociacion entre serial y huella del equipo
- control de maximo de activaciones por licencia
- reinstalacion controlada en el mismo host
- revocacion y renovacion de licencias anuales

### Enfoque recomendado

- mantener el modelo local firmado ya existente
- evolucionar a un esquema `offline-first` con validacion central

### Plataformas candidatas

- `Supabase`
  - recomendada como primera opcion
  - mejor ajuste para tablas de licencias, activaciones, instalaciones y auditoria
- `Firebase`
  - alternativa viable
  - especialmente util si el producto evoluciona a paneles web, push o ecosistemas moviles

---

## 2. Evolucion de supervision visual

- mayor madurez del mosaico multi-camara
- perfiles por fabricante
- mejor soporte RTSP en laboratorio y produccion
- deteccion de imagen congelada

---

## 3. Hardening y reputacion binaria

- firma digital de ejecutable e instalador
- mejoras anti-tamper adicionales
- revision de logs y almacenamiento defensivo
- validacion de release en entornos Windows limpios

---

## 4. Evolucion operativa

- mas presets por tipo de instalacion
- paneles ejecutivos mas amplios
- reportes automatizados por cliente o instalacion
- futuras integraciones de correo o canales externos complementarios

---

## 5. Exploracion tecnica separada

- evaluacion de Nuitka en rama independiente
- comparativa de tamano, compatibilidad y dificultad de mantenimiento

---

**Producto:** Anvic Network Sentinel  
**Version de referencia:** 2.2.1  
**Estado:** Roadmap futuro documentado
