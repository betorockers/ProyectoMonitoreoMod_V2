# Plan de Orden para Anvic Network Sentinel

## Objetivo

Ordenar la base del proyecto sin destruir lo que ya funciona, manteniendo la identidad de **Anvic Network Sentinel** y evitando que el refactor termine rompiendo seguridad, persistencia o flujo operativo.

Este documento no propone “rehacer todo”.
Propone tomar control del crecimiento orgánico del sistema.

---

## Diagnóstico Base

La aplicación nació como monitor de equipos en red y fue creciendo con:

- historial
- métricas
- usuarios
- alertas
- diagnóstico
- backups
- reportes
- empaquetado

Eso no es malo.
De hecho, es señal de que la app fue útil.

El problema apareció cuando el producto siguió creciendo más rápido que su estructura interna. Entonces quedaron:

- nombres mezclados
- módulos duplicados
- lógica vieja y nueva conviviendo
- persistencias distintas
- caminos paralelos para resolver el mismo problema

Conclusión:

el proyecto no está mal encaminado;
está **sobrecargado por evolución acumulada**.

---

## Qué Hay Que Conservar Sí o Sí

Estas son las piezas que conviene tratar como “patrimonio del producto”.

## 1. Identidad del producto

En esta versión, la identidad oficial a preservar debe ser:

- **Nombre:** `Anvic Network Sentinel`
- imagen corporativa alineada a Anvic
- branding, logos, íconos y textos coherentes con ese nombre

Todo lo que huela a `Argos Guard` o naming intermedio debe tratarse como rastro de transición, no como identidad vigente de esta versión.

## 2. Núcleo funcional real

Hay que conservar el corazón operativo que sí resuelve el problema original:

- monitoreo por IP
- estado conectado/desconectado
- lectura de MAC cuando aplica
- intervalos configurables
- tarjetas de estado
- persistencia de equipos monitoreados

Ese núcleo es la razón de existir del sistema.

## 3. Funciones que ya agregan valor real

Estas funcionalidades ya justifican el crecimiento del producto y no deberían eliminarse:

- historial de latencia y disponibilidad
- uptime y métricas
- alertas visuales/sonoras
- alertas Telegram
- generación de reportes
- backups
- gestión de usuarios
- herramientas de diagnóstico de red

No son “adorno”.
Ya forman parte del valor real del software.

## 4. Lo que ya está bien resuelto

Hay piezas que conviene rescatar como base aunque luego se reorganicen:

- uso de SQLite para métricas
- uso de `customtkinter`
- separación visual por tabs
- utilidad de `utils/paths.py`
- idea de modularizar `services`, `database`, `ui`, `core`

---

## Qué Está Mezclado, Duplicado o Peligroso

Aquí está el verdadero foco del desorden.

## 1. Dos arquitecturas al mismo tiempo

Hoy conviven:

- una base vieja/monolítica real
- una base nueva/modular incompleta

Síntoma claro:

- `main.py` sigue arrancando `monitor.py`
- pero ya existe `core/app.py` como nueva dirección

Esto genera:

- duplicación de trabajo
- confusión
- riesgo de tocar una rama y creer que cambiaste la app real

## 2. Duplicación de módulos

Existen versiones viejas y nuevas de piezas clave:

- auth
- ping
- métricas
- herramientas de red
- app principal

También existe carpeta `legacy/`, lo que confirma que el proyecto ya arrastra varias capas históricas.

## 3. Naming mezclado

Aparecen nombres como:

- Anvic Network Sentinel
- Anvic Network Monitor
- Argos Guard
- Sentinel

Esto afecta:

- branding
- copy de UI
- documentación
- instalador
- percepción de madurez

## 4. Seguridad inconsistente entre ramas

La rama activa parece tener medidas más fuertes en algunos puntos:

- cifrado con `Fernet`
- DPAPI
- `bcrypt`

Mientras que la rama modular nueva simplifica cosas que no conviene simplificar todavía.

Esto significa que refactorizar “hacia lo nuevo” sin cuidado puede empeorar el sistema.

## 5. Persistencia heterogénea

Hoy aparecen múltiples formatos y archivos:

- SQLite
- JSON plano
- JSON cifrado
- `.enc`
- `.bak`
- `.corrupt`

Eso es manejable por ahora, pero no sostenible si el sistema sigue creciendo.

## 6. Release y repo con ruido

Hay señales de proyecto todavía no saneado del todo:

- conflicto de merge en `installer.iss`
- artefactos operativos mezclados con el workspace
- respaldos y datos reales viviendo cerca del código fuente

---

## En Qué Orden Conviene Meter Mano

Este es el orden que yo recomiendo cuando arranquemos “todo el viaje”.

## Fase 1: Definir la verdad oficial del producto

Primero hay que fijar una sola verdad para estas preguntas:

- ¿Cuál es el nombre oficial? `Anvic Network Sentinel`
- ¿Cuál es el branding oficial?
- ¿Cuál es la app real que arranca?
- ¿Cuál es el formato oficial de usuarios/configuración/métricas?
- ¿Qué carpetas son oficiales y cuáles quedan como legado temporal?

Sin esta decisión, cualquier mejora técnica va a seguir construida sobre arena.

### Resultado esperado de esta fase

- una identidad única
- una arquitectura elegida
- una lista clara de componentes vigentes y componentes heredados

## Fase 2: Congelar el crecimiento desordenado

Antes de agregar más funciones:

- dejar de crear nuevas variantes del mismo módulo
- dejar de duplicar lógica
- dejar de mezclar naming nuevo y viejo

Objetivo:

detener la expansión del desorden antes de ordenar.

## Fase 3: Elegir el núcleo oficial

Aquí hay una decisión grande:

### Opción A

Tomar `monitor.py` como base oficial temporal y limpiar desde ahí.

Ventajas:

- menor riesgo inmediato
- trabajas sobre lo que realmente corre hoy

Desventajas:

- sigues montado sobre un monolito grande

### Opción B

Completar la migración hacia la arquitectura modular y luego mover `main.py`.

Ventajas:

- base más mantenible a futuro

Desventajas:

- más riesgo de regresión si no se migra seguridad y persistencia correctamente

### Mi recomendación

Yo no haría una migración brusca.
Primero limpiaría y alinearía comportamiento.
Luego movería el entrypoint cuando la rama modular tenga paridad funcional real.

## Fase 4: Unificar seguridad y persistencia

Antes de adoptar la arquitectura nueva como oficial, hay que garantizar que conserve o mejore:

- autenticación
- almacenamiento de usuarios
- cifrado de configuración sensible
- rutas de datos
- compatibilidad de carga

La regla debe ser:

**ordenar sí, retroceder en seguridad no.**

## Fase 5: Separar producto, datos y legado

Aquí conviene dejar tres territorios claros:

- código vigente
- datos/runtime
- legado o respaldo

Eso reduce muchísimo el ruido mental y el riesgo de errores raros.

## Fase 6: Recién ahí seguir creciendo

Una vez ordenado lo anterior, ya sí conviene seguir con:

- mejoras visuales
- nuevas herramientas
- más automatización
- más reportes
- nuevas integraciones

---

## Qué Haría Yo Primero en la Práctica

Si empezáramos ahora mismo a trabajar de verdad, mi secuencia inicial sería esta:

1. consolidar naming y branding a `Anvic Network Sentinel`
2. inventariar archivos vigentes vs legado
3. decidir si `monitor.py` sigue siendo núcleo temporal oficial
4. alinear seguridad y persistencia entre viejo y nuevo
5. cerrar conflicto del instalador
6. recién después mover módulos o entrypoints

---

## Qué No Conviene Hacer

Hay varias tentaciones que sería mejor evitar:

## 1. No conviene “rehacer desde cero”

Perderías mucho valor ya ganado.

## 2. No conviene migrar de golpe al sistema modular

Podrías romper funciones reales que hoy ya sirven.

## 3. No conviene seguir agregando features sin ordenar

Cada feature nueva en este estado va a costar más de lo que debería.

## 4. No conviene borrar legado sin mapear dependencias

Primero hay que entender qué está activo, qué está muerto y qué solo parece muerto.

---

## Mi Recomendación Sincera

La estrategia correcta para este proyecto no es “romper para ordenar”.

La estrategia correcta es:

- reconocer que el software creció porque era útil
- respetar lo que ya funciona
- elegir una identidad oficial
- consolidar el núcleo
- podar duplicaciones
- recién después seguir expandiendo

En simple:

no hace falta matar el proyecto para salvarlo;
hace falta **disciplinar su crecimiento**.

---

## Cierre

Anvic Network Sentinel ya tiene suficiente valor como para tratarlo como producto serio.

No necesita una revolución.
Necesita una etapa de orden.

Si hacemos bien ese orden, el proyecto deja de ser “una app que fue acumulando cosas” y pasa a ser una plataforma de monitoreo sólida, coherente y mantenible.
