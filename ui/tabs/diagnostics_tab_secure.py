import json
import os

import customtkinter

from config.settings import SERVICES_WHITELIST_FILE
from ui.tabs.diagnostics_tab import DiagnosticsTab as BaseDiagnosticsTab
from utils.paths import get_base_path


class DiagnosticsTab(BaseDiagnosticsTab):
    """Extiende la tab de diagnostico con una visualizacion mas clara de servicios."""

    def _load_services(self) -> None:
        for widget in self.services_container.winfo_children():
            widget.destroy()
        self.service_widgets = {}
        try:
            data = self._read_services_config()

            for service in data.get("services", []):
                name = service["name"]
                display_name = service.get("display_name") or name
                description = service.get("description", "")

                row = customtkinter.CTkFrame(self.services_container, fg_color="#303030")
                row.pack(fill="x", pady=3)

                text_frame = customtkinter.CTkFrame(row, fg_color="transparent")
                text_frame.pack(side="left", fill="x", expand=True, padx=(8, 4), pady=6)

                customtkinter.CTkLabel(
                    text_frame,
                    text=display_name,
                    font=("Arial", 12, "bold"),
                    anchor="w",
                    text_color="#FFFFFF",
                ).pack(fill="x", anchor="w")

                customtkinter.CTkLabel(
                    text_frame,
                    text=f"Servicio Windows: {name}",
                    font=("Arial", 10, "italic"),
                    anchor="w",
                    justify="left",
                    text_color="#8F96A3",
                ).pack(fill="x", anchor="w", pady=(1, 0))

                if description:
                    customtkinter.CTkLabel(
                        text_frame,
                        text=description,
                        font=("Arial", 11),
                        anchor="w",
                        justify="left",
                        wraplength=520,
                        text_color="#B8BDC7",
                    ).pack(fill="x", anchor="w", pady=(2, 0))

                status_label = customtkinter.CTkLabel(
                    row,
                    text="...",
                    width=80,
                    text_color="#DDDDDD",
                )
                status_label.pack(side="left", padx=5)

                customtkinter.CTkButton(
                    row,
                    text="Iniciar",
                    width=70,
                    command=lambda n=name: self._svc_act(n, "start"),
                ).pack(side="left", padx=(4, 2))

                customtkinter.CTkButton(
                    row,
                    text="Detener",
                    width=70,
                    fg_color="#ff6b6b",
                    hover_color="#e03131",
                    command=lambda n=name: self._svc_act(n, "stop"),
                ).pack(side="left", padx=(2, 8))

                customtkinter.CTkButton(
                    row,
                    text="Quitar",
                    width=65,
                    fg_color="#495057",
                    hover_color="#343a40",
                    command=lambda n=name: self._remove_service_entry(n),
                ).pack(side="left", padx=(0, 8))

                self.service_widgets[name] = {"status_label": status_label}

            if not self.service_widgets:
                customtkinter.CTkLabel(
                    self.services_container,
                    text="No hay servicios configurados para supervision local.",
                    text_color="#B8BDC7",
                    justify="left",
                ).pack(anchor="w", padx=8, pady=8)

            self.app.after(500, self._refresh_all_services)
        except Exception as exc:
            customtkinter.CTkLabel(
                self.services_container,
                text=f"No se pudo cargar la lista de servicios.\n{exc}",
                text_color="#ff6b6b",
                justify="left",
            ).pack(anchor="w", padx=8, pady=8)
