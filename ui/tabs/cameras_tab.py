"""Pestana base para gestion y prueba de camaras IP."""

import io
import threading

import customtkinter

from services.camera_tools import CameraTools
from ui.components.toast import ToastNotification

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class CamerasTab:
    """Gestiona perfiles de camaras, pruebas y video en vivo."""

    def __init__(self, app, tab_frame):
        self.app = app
        self.frame = tab_frame
        self.camera_map: dict[str, dict] = {}
        self.test_preview_image = None
        self.live_preview_image = None
        self.live_refresh_after_id = None
        self.live_stream_active = False
        self.live_stream_mode = "snapshot"
        self.mosaic_sessions: dict[str, dict] = {}
        self.mosaic_preview_images: dict[str, object] = {}
        self.frame.bind("<Destroy>", self._on_frame_destroy, add="+")
        self._build_ui()
        self._refresh_camera_list()

    def _build_ui(self) -> None:
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.sub_tabs = customtkinter.CTkTabview(self.frame, fg_color="transparent")
        self.sub_tabs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        tab_profiles = self.sub_tabs.add("Perfiles y Pruebas")
        tab_live = self.sub_tabs.add("Video en Vivo")

        self._build_profiles_tab(tab_profiles)
        self._build_live_tab(tab_live)

    def _build_profiles_tab(self, master) -> None:
        master.grid_columnconfigure(0, weight=0)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)

        left = customtkinter.CTkScrollableFrame(master, width=320)
        left.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ns")

        right = customtkinter.CTkFrame(master)
        right.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)
        right.grid_rowconfigure(6, weight=1)

        customtkinter.CTkLabel(
            left, text="Perfiles de Camara", font=("Arial", 16, "bold")
        ).pack(padx=15, pady=(15, 10), anchor="w")

        self.camera_option = customtkinter.CTkOptionMenu(
            left,
            values=["Sin camaras"],
            width=260,
            command=lambda _: self._load_selected_camera(),
        )
        self.camera_option.pack(padx=15, pady=(0, 10), fill="x")

        customtkinter.CTkButton(
            left, text="Cargar perfil", command=self._load_selected_camera
        ).pack(padx=15, pady=4, fill="x")

        self.name_entry = customtkinter.CTkEntry(
            left, placeholder_text="Nombre de camara"
        )
        self.name_entry.pack(padx=15, pady=4, fill="x")

        self.ip_entry = customtkinter.CTkEntry(left, placeholder_text="IP o host")
        self.ip_entry.pack(padx=15, pady=4, fill="x")

        self.snapshot_entry = customtkinter.CTkEntry(
            left, placeholder_text="URL snapshot HTTP/HTTPS"
        )
        self.snapshot_entry.pack(padx=15, pady=4, fill="x")

        self.rtsp_entry = customtkinter.CTkEntry(left, placeholder_text="URL RTSP")
        self.rtsp_entry.pack(padx=15, pady=4, fill="x")

        self.username_entry = customtkinter.CTkEntry(left, placeholder_text="Usuario")
        self.username_entry.pack(padx=15, pady=4, fill="x")

        self.password_entry = customtkinter.CTkEntry(
            left, placeholder_text="Contrasena", show="*"
        )
        self.password_entry.pack(padx=15, pady=4, fill="x")

        customtkinter.CTkButton(
            left, text="Guardar perfil", command=self._save_camera_profile
        ).pack(padx=15, pady=(10, 4), fill="x")

        customtkinter.CTkButton(
            left,
            text="Eliminar perfil",
            fg_color="#b33939",
            hover_color="#962d22",
            command=self._remove_selected_camera,
        ).pack(padx=15, pady=4, fill="x")

        customtkinter.CTkButton(
            left,
            text="Enviar a Video en Vivo",
            fg_color="#1f6feb",
            hover_color="#195cc0",
            command=self._sync_profile_to_live_tab,
        ).pack(padx=15, pady=(10, 4), fill="x")

        customtkinter.CTkLabel(
            left,
            text="Usa esta zona para alta de perfiles, snapshot y prueba RTSP.\n"
            "El video continuo vive en su propia subtab.",
            justify="left",
            text_color="#9aa0a6",
            wraplength=270,
        ).pack(padx=15, pady=(12, 15), anchor="w")

        customtkinter.CTkLabel(
            right, text="Pruebas del Perfil", font=("Arial", 16, "bold")
        ).grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        actions = customtkinter.CTkFrame(right, fg_color="transparent")
        actions.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")

        customtkinter.CTkButton(
            actions, text="Probar Snapshot", command=self._probe_snapshot
        ).pack(side="left", padx=(0, 8))

        customtkinter.CTkButton(
            actions, text="Probar RTSP", command=self._probe_rtsp
        ).pack(side="left", padx=(0, 8))

        self.test_preview_label = customtkinter.CTkLabel(
            right,
            text="Sin vista previa cargada",
            fg_color="#1f1f1f",
            corner_radius=12,
            width=720,
            height=360,
        )
        self.test_preview_label.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="nsew")

        self.test_status_box = customtkinter.CTkTextbox(right, height=180)
        self.test_status_box.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.test_status_box.configure(state="disabled")

    def _build_live_tab(self, master) -> None:
        master.grid_columnconfigure(0, weight=0)
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)

        left = customtkinter.CTkScrollableFrame(master, width=320)
        left.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ns")

        right = customtkinter.CTkFrame(master)
        right.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        customtkinter.CTkLabel(
            left, text="Fuente de Video", font=("Arial", 16, "bold")
        ).pack(padx=15, pady=(15, 10), anchor="w")

        self.live_camera_option = customtkinter.CTkOptionMenu(
            left,
            values=["Sin camaras"],
            width=260,
            command=lambda _: self._load_selected_live_camera(),
        )
        self.live_camera_option.pack(padx=15, pady=(0, 10), fill="x")

        customtkinter.CTkButton(
            left, text="Cargar perfil en vivo", command=self._load_selected_live_camera
        ).pack(padx=15, pady=4, fill="x")

        self.live_snapshot_entry = customtkinter.CTkEntry(
            left, placeholder_text="URL snapshot para vivo"
        )
        self.live_snapshot_entry.pack(padx=15, pady=4, fill="x")

        self.live_rtsp_entry = customtkinter.CTkEntry(
            left, placeholder_text="URL RTSP para visor real"
        )
        self.live_rtsp_entry.pack(padx=15, pady=4, fill="x")

        self.live_username_entry = customtkinter.CTkEntry(left, placeholder_text="Usuario")
        self.live_username_entry.pack(padx=15, pady=4, fill="x")

        self.live_password_entry = customtkinter.CTkEntry(
            left, placeholder_text="Contrasena", show="*"
        )
        self.live_password_entry.pack(padx=15, pady=4, fill="x")

        self.live_mode_label = customtkinter.CTkLabel(
            left,
            text="Modo en vivo: auto",
            text_color="#9aa0a6",
        )
        self.live_mode_label.pack(padx=15, pady=(8, 2), anchor="w")

        self.btn_live_start = customtkinter.CTkButton(
            left, text="Iniciar Vivo", command=self._start_live_snapshot
        )
        self.btn_live_start.pack(padx=15, pady=(12, 4), fill="x")

        self.btn_live_stop = customtkinter.CTkButton(
            left,
            text="Detener Vivo",
            fg_color="#b33939",
            hover_color="#962d22",
            state="disabled",
            command=self._stop_live_snapshot,
        )
        self.btn_live_stop.pack(padx=15, pady=4, fill="x")

        self.btn_add_to_mosaic = customtkinter.CTkButton(
            left,
            text="Agregar al Mosaico",
            fg_color="#0f766e",
            hover_color="#115e59",
            command=self._add_selected_camera_to_mosaic,
        )
        self.btn_add_to_mosaic.pack(padx=15, pady=(12, 4), fill="x")

        self.btn_clear_mosaic = customtkinter.CTkButton(
            left,
            text="Limpiar Mosaico",
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self._clear_mosaic,
        )
        self.btn_clear_mosaic.pack(padx=15, pady=4, fill="x")

        customtkinter.CTkLabel(
            left,
            text="Esta subtab queda dedicada para el visor continuo.\n"
            "Si existe RTSP, se prioriza stream real; si no, usa snapshot.\n"
            "Tambien puedes abrir varias fuentes en mosaico dentro del limite configurado.",
            justify="left",
            text_color="#9aa0a6",
            wraplength=270,
        ).pack(padx=15, pady=(12, 15), anchor="w")

        customtkinter.CTkLabel(
            right, text="Video en Vivo", font=("Arial", 16, "bold")
        ).grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        self.stream_status_label = customtkinter.CTkLabel(
            right, text="Streams activos: 0/1", text_color="#9aa0a6"
        )
        self.stream_status_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        self.live_preview_label = customtkinter.CTkLabel(
            right,
            text="Sin video cargado",
            fg_color="#1f1f1f",
            corner_radius=12,
            width=720,
            height=360,
        )
        self.live_preview_label.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="nsew")

        self.live_status_box = customtkinter.CTkTextbox(right, height=180)
        self.live_status_box.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.live_status_box.configure(state="disabled")

        customtkinter.CTkLabel(
            right, text="Mosaico Operacional", font=("Arial", 16, "bold")
        ).grid(row=4, column=0, padx=15, pady=(0, 8), sticky="w")

        self.mosaic_status_label = customtkinter.CTkLabel(
            right,
            text="Sin vistas en mosaico",
            text_color="#9aa0a6",
        )
        self.mosaic_status_label.grid(row=5, column=0, padx=15, pady=(0, 10), sticky="w")

        self.mosaic_frame = customtkinter.CTkScrollableFrame(right, height=260)
        self.mosaic_frame.grid(row=6, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.mosaic_frame.grid_columnconfigure(0, weight=1)
        self.mosaic_frame.grid_columnconfigure(1, weight=1)

    def _refresh_camera_list(self) -> None:
        cameras = getattr(self.app, "cameras_config", [])
        self.camera_map = {
            camera["name"]: camera for camera in cameras if camera.get("name")
        }
        values = list(self.camera_map.keys()) or ["Sin camaras"]
        current_profile = self.camera_option.get() if hasattr(self, "camera_option") else values[0]
        current_live = self.live_camera_option.get() if hasattr(self, "live_camera_option") else values[0]

        self.camera_option.configure(values=values)
        self.live_camera_option.configure(values=values)

        self.camera_option.set(current_profile if current_profile in values else values[0])
        self.live_camera_option.set(current_live if current_live in values else self.camera_option.get())
        for session_name in list(self.mosaic_sessions.keys()):
            if session_name not in self.camera_map:
                self._remove_mosaic_session(session_name)
        self._refresh_stream_status()

    def _load_selected_camera(self) -> None:
        profile = self.camera_map.get(self.camera_option.get())
        if not profile:
            return
        self._apply_profile_to_editor(profile)
        self.live_camera_option.set(profile.get("name", self.live_camera_option.get()))
        self._apply_profile_to_live(profile)
        self._write_status(self.test_status_box, f"Perfil cargado: {profile.get('name', '-')}")

    def _load_selected_live_camera(self) -> None:
        profile = self.camera_map.get(self.live_camera_option.get())
        if not profile:
            return
        self._apply_profile_to_live(profile)
        self._write_status(self.live_status_box, f"Perfil listo para video: {profile.get('name', '-')}")
        self._update_live_mode_label()

    def _sync_profile_to_live_tab(self) -> None:
        profile = self._build_profile_from_editor()
        if not profile.get("name") and not profile.get("host"):
            ToastNotification(self.app, "Camaras", "Carga o completa un perfil antes de enviarlo a video", color="yellow")
            return
        self.live_camera_option.set(profile.get("name") or self.live_camera_option.get())
        self._apply_profile_to_live(profile)
        self.sub_tabs.set("Video en Vivo")
        self._write_status(self.live_status_box, "Perfil sincronizado desde Perfiles y Pruebas")
        self._update_live_mode_label()

    def _save_camera_profile(self) -> None:
        profile = self._build_profile_from_editor()
        name = profile.get("name", "").strip()
        host = profile.get("host", "").strip()
        if not name or not host:
            ToastNotification(
                self.app,
                "Camaras",
                "Nombre e IP/host son obligatorios",
                color="red",
            )
            return

        cameras = [
            cam
            for cam in getattr(self.app, "cameras_config", [])
            if cam.get("name") != name
        ]
        cameras.append(profile)
        self.app.cameras_config = cameras
        self._refresh_camera_list()
        self.camera_option.set(name)
        self.live_camera_option.set(name)
        self._persist_camera_profiles()
        self._write_status(self.test_status_box, f"Perfil guardado: {name}")
        self._update_live_mode_label()
        ToastNotification(
            self.app,
            "Camaras",
            "Perfil de camara actualizado",
            color="green",
        )

    def _remove_selected_camera(self) -> None:
        name = self.camera_option.get()
        cameras = getattr(self.app, "cameras_config", [])
        new_cameras = [cam for cam in cameras if cam.get("name") != name]
        if len(new_cameras) == len(cameras):
            return
        self._stop_live_snapshot()
        self._remove_mosaic_session(name)
        self.app.cameras_config = new_cameras
        self._refresh_camera_list()
        self._clear_form()
        self._persist_camera_profiles()
        self._write_status(self.test_status_box, f"Perfil eliminado: {name}")
        ToastNotification(
            self.app,
            "Camaras",
            "Perfil de camara eliminado",
            color="yellow",
        )

    def _probe_snapshot(self) -> None:
        url = self.snapshot_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not url:
            ToastNotification(
                self.app, "Camaras", "Define una URL de snapshot", color="red"
            )
            return

        self._write_status(self.test_status_box, f"Probando snapshot: {url}")

        def _worker():
            ok, data = CameraTools.fetch_snapshot(
                url,
                username=username,
                password=password,
                verify_tls=getattr(self.app, "verify_tls_certificates", False),
            )
            self.app.after(0, lambda: self._on_snapshot_result(ok, data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_snapshot_result(self, ok: bool, data: dict) -> None:
        if not ok:
            self._write_status(
                self.test_status_box,
                f"Snapshot error:\n{data.get('error', 'Sin detalle')}",
            )
            return

        lines = [
            "Snapshot OK\n",
            f"URL final: {data.get('url', '-')}\n",
            f"HTTP: {data.get('status_code', '-')}\n",
            f"Tiempo: {data.get('elapsed_ms', '-')} ms\n",
            f"Content-Type: {data.get('content_type', '-')}\n",
        ]
        self._write_status(self.test_status_box, "".join(lines))
        self._render_snapshot_preview(
            self.test_preview_label,
            "test_preview_image",
            data.get("image_bytes"),
            empty_text="Sin vista previa cargada",
            status_box=self.test_status_box,
        )

    def _probe_rtsp(self) -> None:
        rtsp_url = self.rtsp_entry.get().strip()
        if not rtsp_url:
            ToastNotification(
                self.app, "Camaras", "Define una URL RTSP", color="red"
            )
            return

        self._write_status(self.test_status_box, f"Probando RTSP: {rtsp_url}")

        def _worker():
            ok, data = CameraTools.probe_rtsp_stream(rtsp_url)
            self.app.after(0, lambda: self._on_rtsp_result(ok, data, self.test_status_box))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_rtsp_result(self, ok: bool, data: dict, target_box) -> None:
        if not ok:
            self._write_status(target_box, f"RTSP error:\n{data.get('error', 'Sin detalle')}")
            return

        state = "abierto" if data.get("open") else "cerrado"
        service = data.get("service") or "sin detectar"
        self._write_status(
            target_box,
            f"RTSP host: {data.get('host', '-')}\n"
            f"Puerto: {data.get('port', '-')}\n"
            f"Estado: {state}\n"
            f"Latencia: {data.get('latency_ms', '-')} ms\n"
            f"Servicio: {service}",
        )

    def _start_live_snapshot(self) -> None:
        snapshot_url = self.live_snapshot_entry.get().strip()
        rtsp_url = self.live_rtsp_entry.get().strip()
        if not snapshot_url and not rtsp_url:
            ToastNotification(
                self.app,
                "Camaras",
                "La vista en vivo requiere URL RTSP o URL de snapshot",
                color="red",
            )
            return
        if self.live_stream_active:
            return
        if not self.app.try_acquire_camera_stream():
            ToastNotification(
                self.app,
                "Streaming",
                f"Se alcanzo el maximo de streams simultaneos ({self.app.camera_max_streams})",
                color="yellow",
            )
            self._refresh_stream_status()
            return

        self.live_stream_active = True
        self.live_stream_mode = "rtsp" if rtsp_url else "snapshot"
        self.btn_live_start.configure(state="disabled")
        self.btn_live_stop.configure(state="normal")
        self._update_live_mode_label()
        self._refresh_stream_status()
        source_label = "RTSP real" if self.live_stream_mode == "rtsp" else "snapshot"
        source_value = rtsp_url if self.live_stream_mode == "rtsp" else snapshot_url
        self._write_status(
            self.live_status_box,
            f"Vista en vivo iniciada\n"
            f"Fuente: {source_label}\n"
            f"Intervalo: {getattr(self.app, 'camera_snapshot_interval', 2)} seg\n"
            f"TLS: {'estricto' if getattr(self.app, 'verify_tls_certificates', False) else 'flexible/autofirmado'}\n"
            f"Origen: {source_value}",
        )
        self._schedule_live_snapshot(0)

    def _stop_live_snapshot(self) -> None:
        if self.live_refresh_after_id is not None:
            try:
                self.app.after_cancel(self.live_refresh_after_id)
            except Exception:
                pass
            self.live_refresh_after_id = None
        if self.live_stream_active:
            self.app.release_camera_stream()
        self.live_stream_active = False
        self.live_stream_mode = "snapshot"
        self.btn_live_start.configure(state="normal")
        self.btn_live_stop.configure(state="disabled")
        self._update_live_mode_label()
        self._refresh_stream_status()

    def _schedule_live_snapshot(self, delay_ms: int | None = None) -> None:
        if not self.live_stream_active:
            return
        if delay_ms is None:
            delay_ms = max(int(getattr(self.app, "camera_snapshot_interval", 2) * 1000), 1000)
        self.live_refresh_after_id = self.app.after(delay_ms, self._live_snapshot_tick)

    def _live_snapshot_tick(self) -> None:
        if not self.live_stream_active:
            return
        url = self.live_snapshot_entry.get().strip()
        rtsp_url = self.live_rtsp_entry.get().strip()
        username = self.live_username_entry.get().strip()
        password = self.live_password_entry.get()

        def _worker():
            if self.live_stream_mode == "rtsp" and rtsp_url:
                ok, data = CameraTools.fetch_rtsp_frame(
                    rtsp_url,
                    username=username,
                    password=password,
                    timeout=max(float(getattr(self.app, "camera_snapshot_interval", 2)), 2.0),
                )
            else:
                ok, data = CameraTools.fetch_snapshot(
                    url,
                    username=username,
                    password=password,
                    verify_tls=getattr(self.app, "verify_tls_certificates", False),
                )
            self.app.after(0, lambda: self._on_live_snapshot_result(ok, data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_live_snapshot_result(self, ok: bool, data: dict) -> None:
        if not self.live_stream_active:
            return
        if ok:
            source_name = "RTSP real" if data.get("source") == "rtsp" else "snapshot"
            self._write_status(
                self.live_status_box,
                f"Video en vivo activo\n"
                f"Fuente: {source_name}\n"
                f"URL final: {data.get('url', '-')}\n"
                f"Tiempo: {data.get('elapsed_ms', '-')} ms\n"
                f"Tamano: {data.get('width', '-')}x{data.get('height', '-')}\n"
                f"HTTP: {data.get('status_code', '-')}\n"
                f"Content-Type: {data.get('content_type', '-')}",
            )
            self._render_snapshot_preview(
                self.live_preview_label,
                "live_preview_image",
                data.get("image_bytes"),
                empty_text="Sin video cargado",
                status_box=self.live_status_box,
            )
        else:
            self._write_status(
                self.live_status_box,
                f"Error en video en vivo:\n{data.get('error', 'Sin detalle')}",
            )
        self._schedule_live_snapshot()

    def _refresh_stream_status(self) -> None:
        active = getattr(self.app, "active_camera_streams", 0)
        max_streams = getattr(self.app, "camera_max_streams", 1)
        self.stream_status_label.configure(text=f"Streams activos: {active}/{max_streams}")
        mosaic_count = len(self.mosaic_sessions)
        if hasattr(self, "mosaic_status_label"):
            self.mosaic_status_label.configure(
                text=(
                    "Sin vistas en mosaico"
                    if mosaic_count == 0
                    else f"Mosaico activo: {mosaic_count} vista(s)"
                )
            )

    def _persist_camera_profiles(self) -> None:
        if hasattr(self.app, "monitor_tab") and hasattr(
            self.app.monitor_tab, "guardar_equipos"
        ):
            self.app.monitor_tab.guardar_equipos()
        elif hasattr(self.app, "guardar_equipos"):
            self.app.guardar_equipos()

    def _build_profile_from_editor(self) -> dict:
        return {
            "name": self.name_entry.get().strip(),
            "host": self.ip_entry.get().strip(),
            "snapshot_url": self.snapshot_entry.get().strip(),
            "rtsp_url": self.rtsp_entry.get().strip(),
            "username": self.username_entry.get().strip(),
            "password": self.password_entry.get(),
        }

    def _apply_profile_to_editor(self, profile: dict) -> None:
        self._set_entry(self.name_entry, profile.get("name", ""))
        self._set_entry(self.ip_entry, profile.get("host", ""))
        self._set_entry(self.snapshot_entry, profile.get("snapshot_url", ""))
        self._set_entry(self.rtsp_entry, profile.get("rtsp_url", ""))
        self._set_entry(self.username_entry, profile.get("username", ""))
        self._set_entry(self.password_entry, profile.get("password", ""))

    def _apply_profile_to_live(self, profile: dict) -> None:
        self._set_entry(self.live_snapshot_entry, profile.get("snapshot_url", ""))
        self._set_entry(self.live_rtsp_entry, profile.get("rtsp_url", ""))
        self._set_entry(self.live_username_entry, profile.get("username", ""))
        self._set_entry(self.live_password_entry, profile.get("password", ""))
        self._update_live_mode_label()

    def _update_live_mode_label(self) -> None:
        rtsp_url = self.live_rtsp_entry.get().strip() if hasattr(self, "live_rtsp_entry") else ""
        snapshot_url = self.live_snapshot_entry.get().strip() if hasattr(self, "live_snapshot_entry") else ""
        if rtsp_url:
            mode_text = "Modo en vivo: RTSP real"
        elif snapshot_url:
            mode_text = "Modo en vivo: snapshot"
        else:
            mode_text = "Modo en vivo: sin fuente"
        if hasattr(self, "live_mode_label"):
            self.live_mode_label.configure(text=mode_text)

    def _build_profile_from_live(self) -> dict:
        selected_name = self.live_camera_option.get().strip()
        return {
            "name": selected_name if selected_name != "Sin camaras" else (self.name_entry.get().strip() or "Camara sin nombre"),
            "host": self.ip_entry.get().strip(),
            "snapshot_url": self.live_snapshot_entry.get().strip(),
            "rtsp_url": self.live_rtsp_entry.get().strip(),
            "username": self.live_username_entry.get().strip(),
            "password": self.live_password_entry.get(),
        }

    def _add_selected_camera_to_mosaic(self) -> None:
        profile = self._build_profile_from_live()
        name = profile.get("name", "").strip()
        if not name:
            ToastNotification(
                self.app,
                "Camaras",
                "Carga un perfil antes de agregarlo al mosaico",
                color="yellow",
            )
            return
        if not profile.get("snapshot_url") and not profile.get("rtsp_url"):
            ToastNotification(
                self.app,
                "Camaras",
                "La camara requiere URL RTSP o snapshot para el mosaico",
                color="red",
            )
            return
        if name in self.mosaic_sessions:
            ToastNotification(
                self.app,
                "Camaras",
                "Esa camara ya esta en el mosaico",
                color="yellow",
            )
            return
        if not self.app.try_acquire_camera_stream():
            ToastNotification(
                self.app,
                "Streaming",
                f"Se alcanzo el maximo de streams simultaneos ({self.app.camera_max_streams})",
                color="yellow",
            )
            self._refresh_stream_status()
            return

        index = len(self.mosaic_sessions)
        row, col = divmod(index, 2)
        card = customtkinter.CTkFrame(self.mosaic_frame)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        self.mosaic_frame.grid_rowconfigure(row, weight=1)

        customtkinter.CTkLabel(
            card,
            text=name,
            font=("Arial", 14, "bold"),
        ).pack(padx=10, pady=(10, 4), anchor="w")

        customtkinter.CTkLabel(
            card,
            text=f"Fuente: {'RTSP real' if profile.get('rtsp_url') else 'snapshot'}",
            text_color="#9aa0a6",
        ).pack(padx=10, pady=(0, 6), anchor="w")

        preview_label = customtkinter.CTkLabel(
            card,
            text="Sin video cargado",
            fg_color="#1f1f1f",
            corner_radius=10,
            width=320,
            height=180,
        )
        preview_label.pack(padx=10, pady=(0, 8))

        status_label = customtkinter.CTkLabel(
            card,
            text="Inicializando vista...",
            justify="left",
            wraplength=300,
            text_color="#d1d5db",
        )
        status_label.pack(padx=10, pady=(0, 8), anchor="w")

        customtkinter.CTkButton(
            card,
            text="Quitar",
            width=90,
            fg_color="#b33939",
            hover_color="#962d22",
            command=lambda n=name: self._remove_mosaic_session(n),
        ).pack(padx=10, pady=(0, 10), anchor="e")

        self.mosaic_sessions[name] = {
            "profile": profile,
            "card": card,
            "preview_label": preview_label,
            "status_label": status_label,
            "after_id": None,
            "active": True,
        }
        self._refresh_stream_status()
        self._schedule_mosaic_session(name, delay_ms=0)
        self._write_status(self.live_status_box, f"Camara agregada al mosaico: {name}")

    def _schedule_mosaic_session(self, session_name: str, delay_ms: int | None = None) -> None:
        session = self.mosaic_sessions.get(session_name)
        if not session or not session.get("active"):
            return
        if delay_ms is None:
            delay_ms = max(int(getattr(self.app, "camera_snapshot_interval", 2) * 1000), 1000)
        session["after_id"] = self.app.after(delay_ms, lambda n=session_name: self._mosaic_tick(n))

    def _mosaic_tick(self, session_name: str) -> None:
        session = self.mosaic_sessions.get(session_name)
        if not session or not session.get("active"):
            return

        profile = session.get("profile", {})
        snapshot_url = profile.get("snapshot_url", "").strip()
        rtsp_url = profile.get("rtsp_url", "").strip()
        username = profile.get("username", "").strip()
        password = profile.get("password", "")
        mode = "rtsp" if rtsp_url else "snapshot"

        def _worker():
            if mode == "rtsp":
                ok, data = CameraTools.fetch_rtsp_frame(
                    rtsp_url,
                    username=username,
                    password=password,
                    timeout=max(float(getattr(self.app, "camera_snapshot_interval", 2)), 2.0),
                )
            else:
                ok, data = CameraTools.fetch_snapshot(
                    snapshot_url,
                    username=username,
                    password=password,
                    verify_tls=getattr(self.app, "verify_tls_certificates", False),
                )
            self.app.after(0, lambda: self._on_mosaic_result(session_name, ok, data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_mosaic_result(self, session_name: str, ok: bool, data: dict) -> None:
        session = self.mosaic_sessions.get(session_name)
        if not session or not session.get("active"):
            return

        label_widget = session["preview_label"]
        status_label = session["status_label"]
        if ok:
            source_name = "RTSP real" if data.get("source") == "rtsp" else "snapshot"
            status_label.configure(
                text=(
                    f"{source_name} | {data.get('elapsed_ms', '-')} ms\n"
                    f"Origen: {data.get('url', '-')}"
                )
            )
            image_attr_name = f"_mosaic_image_{session_name}"
            self._render_snapshot_preview(
                label_widget,
                image_attr_name,
                data.get("image_bytes"),
                empty_text="Sin video cargado",
                max_size=(320, 180),
            )
            self.mosaic_preview_images[session_name] = getattr(self, image_attr_name, None)
        else:
            status_label.configure(text=f"Error: {data.get('error', 'Sin detalle')}")

        self._schedule_mosaic_session(session_name)

    def _remove_mosaic_session(self, session_name: str) -> None:
        session = self.mosaic_sessions.pop(session_name, None)
        if not session:
            return
        after_id = session.get("after_id")
        if after_id is not None:
            try:
                self.app.after_cancel(after_id)
            except Exception:
                pass
        session["active"] = False

        card = session.get("card")
        if card is not None:
            try:
                card.destroy()
            except Exception:
                pass

        self.mosaic_preview_images.pop(session_name, None)
        image_attr_name = f"_mosaic_image_{session_name}"
        if hasattr(self, image_attr_name):
            setattr(self, image_attr_name, None)
        self.app.release_camera_stream()
        self._reflow_mosaic_cards()
        self._refresh_stream_status()

    def _reflow_mosaic_cards(self) -> None:
        for index, session in enumerate(self.mosaic_sessions.values()):
            card = session.get("card")
            if card is None:
                continue
            row, col = divmod(index, 2)
            card.grid_configure(row=row, column=col)
            self.mosaic_frame.grid_rowconfigure(row, weight=1)

    def _clear_mosaic(self) -> None:
        for session_name in list(self.mosaic_sessions.keys()):
            self._remove_mosaic_session(session_name)

    def _on_frame_destroy(self, _event=None) -> None:
        if _event is not None and getattr(_event, "widget", None) is not self.frame:
            return
        if hasattr(self, "live_stream_active"):
            self._stop_live_snapshot()
        if hasattr(self, "mosaic_sessions"):
            self._clear_mosaic()

    def _render_snapshot_preview(
        self,
        label_widget,
        image_attr_name: str,
        image_bytes,
        empty_text: str,
        status_box=None,
        max_size: tuple[int, int] = (720, 360),
    ) -> None:
        if not image_bytes:
            label_widget.configure(text=empty_text, image=None)
            setattr(self, image_attr_name, None)
            return

        if not PIL_AVAILABLE:
            label_widget.configure(text="PIL no disponible para vista previa", image=None)
            setattr(self, image_attr_name, None)
            return

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.thumbnail(max_size)
            preview = customtkinter.CTkImage(
                light_image=image,
                dark_image=image,
                size=image.size,
            )
            setattr(self, image_attr_name, preview)
            label_widget.configure(text="", image=preview)
        except Exception as e:
            label_widget.configure(
                text="Imagen recibida, pero no se pudo renderizar",
                image=None,
            )
            setattr(self, image_attr_name, None)
            if status_box is not None:
                self._write_status(status_box, f"Render error: {e}")

    @staticmethod
    def _write_status(box_widget, text: str) -> None:
        box_widget.configure(state="normal")
        box_widget.delete("1.0", "end")
        box_widget.insert("end", text)
        box_widget.configure(state="disabled")

    @staticmethod
    def _set_entry(entry, value: str) -> None:
        entry.delete(0, "end")
        entry.insert(0, value)

    def _clear_form(self) -> None:
        self._stop_live_snapshot()
        self._clear_mosaic()
        for entry in (
            self.name_entry,
            self.ip_entry,
            self.snapshot_entry,
            self.rtsp_entry,
            self.username_entry,
            self.password_entry,
            self.live_snapshot_entry,
            self.live_rtsp_entry,
            self.live_username_entry,
            self.live_password_entry,
        ):
            entry.delete(0, "end")
        self.test_preview_label.configure(text="Sin vista previa cargada", image=None)
        self.live_preview_label.configure(text="Sin video cargado", image=None)
        self.test_preview_image = None
        self.live_preview_image = None
        self._update_live_mode_label()
