# main.py — Entry point de Anvic Network Sentinel

# Se importa la clase App directamente desde monitor.py, que es el núcleo actual.
# Se pasa una lista vacía para que la aplicación cargue la configuración
# desde el archivo cifrado 'equipos_guardados.json.enc' que acabamos de crear.
from monitor import App

if __name__ == "__main__":
    # Al pasar una lista vacía, forzamos a la App a usar la configuración guardada.
    app = App([])
    app.mainloop()
