# ui/windows/telegram_config.py
"""
Ventana de configuración de alertas de Telegram para Argos Guard.
"""

import customtkinter
from ui.components.toast import ToastNotification


class TelegramConfigWindow(customtkinter.CTkToplevel):
    """Diálogo para configurar o desactivar las alertas de Telegram."""

    def __init__(self, master, current_token: str, current_chat_id: str, on_save):
        super().__init__(master)
        self.on_save = on_save

        self.title("Configuración Telegram")
        self.geometry("400x350")
        self.resizable(False, False)

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"400x350+{(sw-400)//2}+{(sh-350)//2}")

        customtkinter.CTkLabel(
            self, text="🤖 Configuración de Alertas", font=("Arial", 16, "bold")
        ).pack(pady=20)

        self.token_entry = customtkinter.CTkEntry(
            self, placeholder_text="Bot Token", width=300
        )
        self.token_entry.pack(pady=10)
        if current_token:
            self.token_entry.insert(0, current_token)

        self.chat_id_entry = customtkinter.CTkEntry(
            self, placeholder_text="Chat ID", width=300
        )
        self.chat_id_entry.pack(pady=10)
        if current_chat_id:
            self.chat_id_entry.insert(0, current_chat_id)

        customtkinter.CTkLabel(
            self,
            text="Para obtener estos datos, crea un bot con @BotFather\ny obtén tu ID con @userinfobot",
            font=("Arial", 10),
            text_color="gray",
        ).pack(pady=5)

        customtkinter.CTkButton(
            self,
            text="Guardar y Probar",
            command=self._save_config,
            fg_color="#00d9ff", text_color="black",
        ).pack(pady=20)

        customtkinter.CTkButton(
            self,
            text="Desactivar Alertas",
            command=self._disable_alerts,
            fg_color="#ff6b6b",
        ).pack(pady=5)

    def _save_config(self) -> None:
        token = self.token_entry.get().strip()
        chat_id = self.chat_id_entry.get().strip()

        if not token or not chat_id:
            ToastNotification(self.master, "Error", "Token y Chat ID son requeridos", color="red")
            return

        self.on_save(token, chat_id)
        ToastNotification(
            self.master, "Guardado", "Configuración actualizada. Enviando prueba...", color="green"
        )
        self.destroy()

    def _disable_alerts(self) -> None:
        self.on_save("", "")
        ToastNotification(
            self.master, "Desactivado", "Alertas de Telegram desactivadas", color="yellow"
        )
        self.destroy()
