import os
from PIL import Image, ImageDraw

def create_argos_icon():
    # Asegurar que el directorio existe
    output_dir = os.path.join("assets", "img")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    size = (256, 256)
    # Crear imagen transparente
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colores (Azul tecnológico Sentinel)
    shield_fill = "#0f172a"   # Azul oscuro de fondo
    shield_outline = "#00d9ff" # Cyan brillante (mismo del login)
    node_color = "#ffffff"    # Blanco
    line_color = "#00d9ff"    # Cyan

    # --- Dibujar Escudo ---
    w, h = size
    # Coordenadas para un escudo moderno
    points = [
        (w*0.5, h*0.95),  # Punta inferior
        (w*0.15, h*0.4),  # Lado izquierdo curva
        (w*0.15, h*0.15), # Esquina superior izq
        (w*0.5, h*0.2),   # Centro superior (leve pico hacia abajo)
        (w*0.85, h*0.15), # Esquina superior der
        (w*0.85, h*0.4),  # Lado derecho curva
    ]
    
    # Relleno del escudo
    draw.polygon(points, fill=shield_fill)
    
    # Borde del escudo (dibujamos líneas gruesas manualmente para simular stroke)
    draw.line(points + [points[0]], fill=shield_outline, width=10)

    # --- Dibujar Red (Nodos conectados) ---
    nodes = [
        (w*0.5, h*0.45),  # Centro
        (w*0.35, h*0.65), # Izq abajo
        (w*0.65, h*0.65), # Der abajo
        (w*0.5, h*0.30)   # Arriba
    ]
    
    # Conexiones entre nodos
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            draw.line([nodes[i], nodes[j]], fill=line_color, width=4)
            
    # Dibujar los nodos (puntos)
    r = 15 # Radio del nodo
    for nx, ny in nodes:
        draw.ellipse((nx-r, ny-r, nx+r, ny+r), fill=shield_fill, outline=node_color, width=4)

    # --- Guardar Archivos ---
    png_path = os.path.join(output_dir, "icono_argos.png")
    ico_path = os.path.join(output_dir, "icono_argos.ico")
    logo_path = os.path.join(output_dir, "logoargosguard.png")
    
    # Guardar PNG
    img.save(png_path)
    img.save(logo_path)
    
    # Guardar ICO (contiene varios tamaños para Windows)
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    
    print(f"✅ Iconos generados exitosamente:")
    print(f" - {png_path}")
    print(f" - {logo_path}")
    print(f" - {ico_path}")

if __name__ == "__main__":
    create_argos_icon()
