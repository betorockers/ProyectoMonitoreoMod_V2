# Inventario de Lotes de Licencias v2.2
## Anvic Network Sentinel

Ubicación de los lotes emitidos:

- `.secrets/license_batches/v2_2/standard_perpetual.csv`
- `.secrets/license_batches/v2_2/advanced_perpetual.csv`
- `.secrets/license_batches/v2_2/pro_perpetual.csv`
- `.secrets/license_batches/v2_2/standard_annual.csv`
- `.secrets/license_batches/v2_2/advanced_annual.csv`
- `.secrets/license_batches/v2_2/pro_annual.csv`
- `.secrets/license_batches/v2_2/standard_trial_30d.csv`
- `.secrets/license_batches/v2_2/advanced_trial_30d.csv`
- `.secrets/license_batches/v2_2/pro_trial_30d.csv`

## Cantidades emitidas

### Perpetual

- Standard: 334
- Advanced: 333
- Pro: 333
- Total perpetuas: 1000

### Annual

- Standard: 334
- Advanced: 333
- Pro: 333
- Total anuales: 1000

### Trial 30 días

- Standard: 10
- Advanced: 10
- Pro: 10
- Total trial: 30

## Observación importante

El serial visible emitido comienza con `ANS1.` y la diferenciación por edición y vigencia queda resuelta en:

- el `license_id`
- el payload firmado de la licencia
- el archivo CSV del lote correspondiente

Ejemplos de `license_id`:

- `STA-PER-0001`
- `ADV-ANN-0001`
- `PRO-TRI-0001`

## Resguardo

- La clave privada de firma permanece en `.secrets/licensing/`
- Estos lotes no deben publicarse ni incluirse en builds
- La distribución al cliente debe hacerse desde copias controladas

---

**Producto:** Anvic Network Sentinel  
**Versión:** 2.2  
**Fecha de emisión:** Marzo 2026
