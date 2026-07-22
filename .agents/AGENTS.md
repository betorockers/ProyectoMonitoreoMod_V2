# Workspace Customizations

## Rules
- **Gestión de Planes de Implementación y Walkthroughs**: Todos los archivos de planes de implementación (`implementation_plan.md`) y walkthroughs (`walkthrough.md`) obligatoriamente deben ser guardados/copiados en la carpeta `estudio y mejoras` en la raíz del proyecto. Si la carpeta no existe, créala.
- **PROTOCOLO ESTRICTO DE COMPILACIÓN BAJO AUTORIZACIÓN EXPRESA**: NUNCA ejecutar scripts de compilación (`build_v4.ps1`, Nuitka) ni generar instaladores (`installer_v4.iss`) sin que el usuario dé la orden explícita e inequívoca.
- **PROTOCOLO OBLIGATORIO DE SUITE DE PRUEBAS EN DESARROLLO**: Tras completar la construcción de módulos y antes de proponer compilación, se debe ejecutar secuencialmente:
  1. **Pruebas Unitarias y Módulos (`pytest`)**: Evaluación exhaustiva de cada app y función en `backend_v4`.
  2. **Pruebas de Estrés (`k6`)**: Carga de concurrencia y estrés de endpoints/vistas.
  3. **Pruebas End-to-End (`Playwright` + Chrome DevTools MCP)**: Validación visual de flujos de usuario y renderizado HTMX/Alpine.js.
  4. **Pruebas del Usuario en Vivo**: Entregar entorno de desarrollo activo para revisión personal del usuario antes de proceder a producción.
- **Compilación Autónoma y Empaquetado 100% Autocontenido**: Todo ejecutable e instalador de este proyecto DEBE incluir explícitamente el 100% de las dependencias Python, submódulos dinámicos, binarios C/C++ (`sqlcipher3`, `PyQt6` WebEngine, DLLs `d3dcompiler_47.dll`, `opengl32sw.dll`), plugins Nuitka (`pyqt6`, `matplotlib`, `numpy`), archivos de datos de paquetes (`limits`, `fpdf`, `matplotlib`, `seaborn`, `pandas`, `dns`), e instaladores desatendidos de C++ Runtime y Google Chrome.
- **Orquestación Obligatoria con Agentes de Agencia**: Todo el trabajo y tareas de este proyecto DEBE estar siempre ("sí o sí") orquestado mediante el uso de los agentes ubicados en el directorio `E:\agency-agents`. Cada agente debe cumplir con sus tareas correspondientes, delegando el trabajo según sus especialidades en lugar de resolver todo monolíticamente.
- **Registro Centralizado de Diagnósticos y Pruebas**: Todos los reportes de pruebas (Unitarias, Estrés, E2E) y los diagnósticos/fallas encontrados (incluyendo sus resoluciones) DEBEN obligatoriamente guardarse en formato `.md` dentro de la carpeta `diagnosticos_y_pruebas` en la raíz del proyecto. Si la carpeta no existe, debe crearse.
