from __future__ import annotations

import customtkinter

from config.branding import APP_NAME


class LicenseActivationWindow(customtkinter.CTkToplevel):
    def __init__(self, master, on_activate, on_cancel, machine_code: str, initial_message: str = ""):
        super().__init__(master)
        self.on_activate = on_activate
        self.on_cancel = on_cancel
        self.title(f"{APP_NAME} - Activacion")
        self.geometry("560x500")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._handle_cancel)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 560) // 2
        y = (screen_height - 500) // 2
        self.geometry(f"560x500+{x}+{y}")

        customtkinter.CTkLabel(
            self,
            text="Activacion de licencia",
            font=("Arial", 24, "bold"),
            text_color="#00d9ff",
        ).pack(pady=(30, 12))

        customtkinter.CTkLabel(
            self,
            text=(
                "Ingrese un serial firmado para habilitar esta instalacion. "
                "La activacion se vinculara al equipo actual y validara edicion, tipo y vigencia."
            ),
            wraplength=470,
            justify="left",
            text_color="#CCCCCC",
            font=("Arial", 13),
        ).pack(pady=(0, 14))

        customtkinter.CTkLabel(
            self,
            text=f"Huella del equipo: {machine_code}",
            font=("Consolas", 12),
            text_color="#FFD43B",
        ).pack(pady=(0, 12))

        self.message_label = customtkinter.CTkLabel(
            self,
            text=initial_message,
            wraplength=470,
            justify="left",
            text_color="#AAAAAA",
            font=("Arial", 12),
        )
        self.message_label.pack(pady=(0, 10))

        self.serial_box = customtkinter.CTkTextbox(self, width=500, height=210)
        self.serial_box.pack(pady=10, padx=30, fill="both", expand=False)

        self.button_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=30, pady=(10, 20))
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        self.activate_button = customtkinter.CTkButton(
            self.button_frame,
            text="Activar licencia",
            command=self._handle_activate,
            fg_color="#00d9ff",
            text_color="#0F172A",
            hover_color="#6ee7ff",
            height=42,
        )
        self.activate_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.cancel_button = customtkinter.CTkButton(
            self.button_frame,
            text="Salir",
            command=self._handle_cancel,
            fg_color="#374151",
            hover_color="#4B5563",
            height=42,
        )
        self.cancel_button.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _handle_activate(self):
        serial = self.serial_box.get("1.0", "end").strip()
        self.on_activate(serial)

    def _handle_cancel(self):
        self.on_cancel()
