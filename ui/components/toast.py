# ui/components/toast.py
"""
Componente de notificación tipo Toast para Argos Guard.
Muestra alertas no intrusivas en la esquina inferior derecha de la pantalla.
"""

import customtkinter


class ToastNotification(customtkinter.CTkToplevel):
    """
    Ventana de notificación flotante estilo Toast.
    Se auto-destruye después del tiempo especificado.
    """

    def __init__(
        self,
        master,
        title: str,
        message: str,
        color: str = "green",
        duration: int = 5000,
    ):
        super().__init__(master)

        # Aplicar icono diferido para evitar glitches de Tkinter
        self.after(200, lambda: self._apply_icon(master))

        self.overrideredirect(True)   # Sin bordes de ventana
        self.attributes("-topmost", True)

        # Colores según el tipo de alerta
        bg_color = "#1A1A1A"
        color_map = {
            "green": "#51cf66",
            "red": "#ff6b6b",
            "yellow": "#ffd43b",
            "blue": "#339af0",
        }
        border_color = color_map.get(color, "#51cf66")

        self.configure(fg_color=bg_color)

        # Posición: esquina inferior derecha
        width, height = 350, 100
        x = self.winfo_screenwidth() - width - 20
        y = self.winfo_screenheight() - height - 60
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Frame principal con borde coloreado
        main_frame = customtkinter.CTkFrame(
            self,
            corner_radius=10,
            border_width=2,
            border_color=border_color,
            fg_color=bg_color,
        )
        main_frame.pack(fill="both", expand=True)

        # Ícono y Título
        icon = "🛡️" if color == "green" else "⚠️"
        customtkinter.CTkLabel(
            main_frame,
            text=f"{icon} {title}",
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF",
        ).pack(pady=(10, 0), padx=15, anchor="w")

        # Mensaje
        customtkinter.CTkLabel(
            main_frame,
            text=message,
            font=("Arial", 12),
            text_color="#CCCCCC",
            wraplength=300,
            justify="left",
        ).pack(pady=(5, 10), padx=15, anchor="w")

        # Barra de progreso decorativa
        customtkinter.CTkProgressBar(
            main_frame, height=4, progress_color=border_color
        ).pack(fill="x", padx=15, pady=(0, 10))

        # Auto-cierre
        self.after(duration, self.destroy)

    def _apply_icon(self, master) -> None:
        """Hereda el icono de la ventana maestra si está disponible."""
        try:
            # Subir en la jerarquía hasta encontrar la ventana raíz con icono
            root = master
            while root.master is not None:
                root = root.master
            if hasattr(root, "_icon_path") and root._icon_path:
                self.iconbitmap(root._icon_path)
        except Exception:
            pass
