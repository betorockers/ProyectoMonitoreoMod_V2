# Plan de Optimización de Layout y Responsividad

Este plan detalla los ajustes necesarios para que la aplicación se vea estética y funcionalmente bien en el tamaño predeterminado de 1366x768, y que los componentes se adapten correctamente cuando el usuario amplíe o maximice la ventana.

## Cambios Propuestos

### [Componente] monitor.py

#### [MODIFY] [monitor.py](file:///d:/respaldo_de_todo_anvic/entrenamiento/Proyectos/ProyectoMonitoreoMod_V2/monitor.py)

1.  **Optimización de [IPMonitor](file:///d:/respaldo_de_todo_anvic/entrenamiento/Proyectos/ProyectoMonitoreoMod_V2/monitor.py#21-122) (Tarjetas):**
    *   Ajustar el tamaño de las fuentes y espaciados para que las tarjetas sean más compactas pero legibles.
    *   Asegurar que el borde y los iconos escalen visualmente bien.

2.  **Optimización de [App](file:///d:/respaldo_de_todo_anvic/entrenamiento/Proyectos/ProyectoMonitoreoMod_V2/monitor.py#123-512) (Layout General):**
    *   **Sidebar:** Mantener un ancho fijo razonable (ej. 200-240px) para que no ocupe demasiado espacio en 1366px.
    *   **Tabview:** Asegurar que use todo el espacio disponible (`sticky="nsew"`).
    *   **Monitor Frame (Grid):** 
        *   Ajustar el número de columnas dinámicamente o asegurar que las tarjetas se expandan proporcionalmente.
        *   Usar `weight=1` en las columnas del grid para que se distribuyan uniformemente.

3.  **Optimización de Pestaña Historial:**
    *   **Gráfico de Latencia:** Ajustar el `figsize` para que encaje mejor en la resolución 1366x768 sin necesidad de mucho scroll vertical.
    *   **Gauges:** Organizar los gauges en un grid responsivo en lugar de una fila simple (`side="left"`), para que se acomoden si hay muchos equipos.
    *   **Tabla de Eventos:** Asegurar que el `CTkTextbox` se expanda correctamente.

## Plan de Verificación

### Verificación Manual
1.  **Ejecución Inicial:** Ejecutar `python main.py` y verificar que la ventana se abra en 1366x768 y todos los elementos sean visibles sin scroll innecesario (excepto en el área de monitores si hay muchos).
2.  **Maximización:** Maximizar la ventana y verificar que:
    *   Las tarjetas de monitoreo se expandan o se mantengan centradas estéticamente.
    *   El gráfico de latencia crezca para ocupar el nuevo espacio.
    *   Los gauges se reposicionen o escalen correctamente.
3.  **Pestañas:** Cambiar entre pestañas y verificar que el layout se mantenga consistente.
