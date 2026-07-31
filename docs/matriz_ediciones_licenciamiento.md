# Matriz Final de Ediciones y Licenciamiento
## Anvic Network Sentinel

Este documento establece la estructura comercial y funcional de las licencias de **Anvic Network Sentinel**, diferenciando claramente:

- la **edición** del producto
- el **tipo de licencia**
- el **prefijo de serial**
- el **uso recomendado**

---

## 1. Ejes del licenciamiento

Anvic Network Sentinel se organiza en dos dimensiones principales:

### Edición funcional

- `STANDARD`
- `ADVANCED`
- `PRO`

### Tipo de licencia

- `TRIAL`
- `ANNUAL`
- `PERPETUAL`

Esto permite combinaciones como:

- `STANDARD TRIAL`
- `STANDARD ANNUAL`
- `ADVANCED PERPETUAL`
- `PRO ANNUAL`
- `PRO TRIAL`

---

## 2. Estructura recomendada del serial

La recomendación es usar un serial visible con prefijo legible para soporte y operación, pero respaldado internamente por una licencia firmada criptográficamente.

Formato visible recomendado:

`ANS1-EDI-TIP-XXXXXXXX`

Donde:

- `ANS1` = esquema de licenciamiento de Anvic Network Sentinel, versión 1
- `EDI` = edición
- `TIP` = tipo de licencia
- `XXXXXXXX` = identificador o bloque emitido

Prefijos recomendados:

- `ANS1-STD-TRY`
- `ANS1-STD-ANN`
- `ANS1-STD-PER`
- `ANS1-ADV-TRY`
- `ANS1-ADV-ANN`
- `ANS1-ADV-PER`
- `ANS1-PRO-TRY`
- `ANS1-PRO-ANN`
- `ANS1-PRO-PER`

Nota: el prefijo facilita identificación humana, pero la validez real de la licencia debe depender del **payload firmado** y no solo del texto visible.

---

## 3. Tipos de licencia

## Trial

- vigencia de 30 días
- orientada a evaluación, pilotos y testers
- vinculada al equipo anfitrión
- puede emitirse para `STANDARD`, `ADVANCED` o `PRO`
- no reemplaza una licencia comercial

Se recomienda reservar un lote específico para pruebas controladas.  
Actualmente se puede trabajar con un pool inicial de **10 seriales trial** para testers o validaciones internas.

## Annual

- vigencia determinada por fecha de expiración
- apropiada para contratos, renovación anual y control comercial más flexible
- permite control operativo de vencimiento
- ideal para despliegues corporativos con mantenimiento asociado

## Perpetual

- uso permanente de la edición licenciada
- orientada a compra definitiva
- puede complementarse con soporte, mantenimiento o actualizaciones por separado

---

## 4. Matriz funcional por edición

## Standard

Edición de entrada orientada a monitoreo base.

Incluye:

- `Operación en Vivo`
- `Historial Operacional`
- monitoreo ICMP
- gestión de equipos
- generación de reportes PDF
- autenticación y administración base
- diagnóstico remoto esencial:
  - `ping`
  - `tracert`
  - `lookup`

Uso recomendado:

- instalaciones pequeñas
- clientes con necesidad de monitoreo básico
- despliegues de entrada o pilotos comerciales controlados

Seriales:

- `ANS1-STD-TRY`
- `ANS1-STD-ANN`
- `ANS1-STD-PER`

## Advanced

Edición profesional para soporte técnico y diagnóstico ampliado.

Incluye todo Standard, más:

- chequeo `HTTP/HTTPS`
- escaneo controlado de puertos
- `SNMP` básico
- `SSH` de consulta
- `Centro de Soporte` completo
- perfiles de cámaras
- pruebas de snapshot
- pruebas RTSP

Uso recomendado:

- operación técnica profesional
- instalaciones con equipos heterogéneos
- clientes que requieren diagnóstico real además de disponibilidad

Seriales:

- `ANS1-ADV-TRY`
- `ANS1-ADV-ANN`
- `ANS1-ADV-PER`

## Pro

Edición de mayor valor comercial y operativo.

Incluye todo Advanced, más:

- `Supervisión Visual` completa
- RTSP real
- vista de `Video en Vivo`
- mosaico multi-cámara
- mayor capacidad de streaming
- mejor aprovechamiento del módulo visual para instalaciones de seguridad

Uso recomendado:

- centros de monitoreo
- operación de seguridad integral
- clientes con CCTV, accesos, LPR, tótems y continuidad operacional
- oferta premium de ANVIC

Seriales:

- `ANS1-PRO-TRY`
- `ANS1-PRO-ANN`
- `ANS1-PRO-PER`

---

## 5. Relación entre edición y vigencia

Es importante separar estos dos conceptos:

- la **edición** define qué funciones puede usar el cliente
- el **tipo de licencia** define por cuánto tiempo puede usar esas funciones

Ejemplos válidos:

- `Standard Annual`
- `Advanced Perpetual`
- `Pro Trial`
- `Pro Annual`

---

## 6. Recomendación operativa de emisión

### Para pilotos o preventa

- `PRO TRIAL` por 30 días
- ideal para mostrar el valor completo del producto

### Para entrada comercial

- `STANDARD ANNUAL`
- `ADVANCED ANNUAL`

### Para cliente corporativo con compra definitiva

- `ADVANCED PERPETUAL`
- `PRO PERPETUAL`

### Para uso interno o grandes cuentas

- licencia corporativa emitida sobre la edición `ADVANCED` o `PRO`
- con control de instalaciones, equipos o derecho comercial según el acuerdo

---

## 7. Recomendación comercial final

- `STANDARD`: entrada al producto
- `ADVANCED`: operación técnica profesional
- `PRO`: supervisión integral y visual con mayor valor de servicio
- `TRIAL`: herramienta de demostración, evaluación y cierre comercial

---

## 8. Criterio de seguridad

La licencia debe distinguir edición y vigencia a nivel de datos firmados, no solo por el texto del serial.  
El serial visible sirve para:

- soporte
- clasificación comercial
- identificación rápida
- trazabilidad operativa

La validación real debe depender del contenido firmado de la licencia.

---

**Producto:** Anvic Network Sentinel  
**Versión de referencia:** 2.2  
**Documento actualizado:** Marzo 2026
