# 🛡️ Estrategia de Seguridad: La Armadura Impenetrable

Este documento detalla la arquitectura de seguridad diseñada para **Argos Guard**, basada en el principio de "Defensa en Profundidad". El objetivo es proteger la integridad de la aplicación, la red donde opera y los datos sensibles que maneja.

---

## 🏛️ Pilar 1: Integridad del Código y Distribución
**Objetivo:** Garantizar que el ejecutable no ha sido alterado y es confiable para el sistema operativo.

### 1.1. Firmado de Código (Code Signing)
- **El Riesgo:** Windows y los antivirus desconfían de ejecutables desconocidos, mostrando alertas de "Editor no verificado" o bloqueando la ejecución.
- **La Solución:**
    - Adquirir un certificado de firma de código (Code Signing Certificate) de una Autoridad de Certificación (CA).
    - Integrar el firmado en el proceso de compilación con PyInstaller.
    - **Resultado:** El ejecutable tendrá una identidad digital verificada, eliminando advertencias de SmartScreen y dificultando la inyección de malware en el binario.

### 1.2. Análisis de Dependencias (Supply Chain Security)
- **El Riesgo:** Vulnerabilidades en librerías de terceros (`requests`, `customtkinter`, etc.) pueden ser explotadas.
- **La Solución:**
    - Implementar escaneos regulares con herramientas como `pip-audit` o Snyk.
    - Mantener un `requirements.txt` con versiones fijas y actualizadas.

---

## 👮 Pilar 2: Seguridad en la Ejecución
**Objetivo:** Limitar el daño potencial por mal uso (interno o externo) y asegurar que la aplicación se comporte como se espera.

### 2.1. Principio de Menor Privilegio (RBAC)
- **Estrategia:**
    - Las herramientas críticas (`net stop`, `ipconfig /release`) están estrictamente restringidas a roles `admin` y `super_admin`.
    - Los usuarios con rol `user` tienen acceso de solo lectura.

### 2.2. Saneamiento y Validación de Entradas (Input Sanitization)
- **El Riesgo:** Inyección de comandos (Command Injection) a través de campos de texto (ej: escribir `8.8.8.8 & del *.*` en el campo de Ping).
- **La Solución:**
    - **Validación Estricta:** Usar Expresiones Regulares (Regex) para validar que la entrada sea exclusivamente una IP o un dominio válido antes de procesarla.
    - **Ejecución Segura:** Uso exclusivo de `subprocess.run` con listas de argumentos (ej: `["ping", ip]`) y **nunca** usar `shell=True`.

### 2.3. Auditoría Forense Expandida
- **Estrategia:**
    - Registrar en `auditoria_usuarios.log` cada ejecución de herramientas de diagnóstico.
    - **Datos a registrar:** Quién (`user`), Qué (`comando`), Cuándo (`timestamp`) y Sobre Qué (`target`).
    - Esto permite rastrear acciones administrativas y detectar abusos.

---

## 🔐 Pilar 3: Seguridad de los Datos en Reposo
**Objetivo:** Proteger la información sensible almacenada en el disco local.

### 3.1. Cifrado de Configuración y Secretos
- **El Riesgo:** Archivos como `equipos_guardados.json` contienen la topología de la red y, críticamente, el **Token de Telegram**. Si son robados, un atacante podría controlar las alertas.
- **La Solución:**
    - Implementar cifrado AES (usando librería `cryptography`) para los archivos JSON sensibles.
    - El archivo en disco será ilegible sin la clave de descifrado interna de la aplicación.
    - **Exportación Segura (Super Admin):** Crear una función exclusiva para el rol `super_admin` que permita generar un reporte PDF corporativo con la configuración descifrada. Esta acción debe requerir re-autenticación (volver a pedir la contraseña) y ser registrada de forma crítica en el log de auditoría.
    - Eliminar cualquier token hardcodeado en el código fuente (`branding.py`).

### 3.2. Protección de la Base de Datos
- **Estrategia:**
    - Aunque SQLite es un archivo local, se debe restringir el acceso a nivel de permisos de archivo del sistema operativo (solo lectura/escritura para el usuario que ejecuta la app).
    - Para entornos de alta seguridad, evaluar el uso de **SQLCipher** para cifrar el archivo `.db` completo.

---

## 🚀 Resumen de Implementación

1.  **Fase Inmediata:** Saneamiento de inputs y Logs de auditoría detallados.
2.  **Fase Corto Plazo:** Cifrado de archivos de configuración (`json`) y Exportación Segura.
3.  **Fase Producción:** Adquisición de certificado y firmado del ejecutable.