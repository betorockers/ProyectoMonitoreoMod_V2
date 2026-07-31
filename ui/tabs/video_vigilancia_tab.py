import os
import cv2
import threading
import datetime
import time
from PIL import Image, ImageTk
import customtkinter

class VideoVigilanciaTab:
    def __init__(self, master_app, parent_frame):
        self.master_app = master_app
        self.parent = parent_frame
        
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1) 
        
        self.cameras = []
        self.active_camera_index = -1
        self.is_playing = False
        self.is_recording = False
        self.video_writer = None
        self.capture_thread = None
        
        self.panel_visible = False
        self.panel_timeout_id = None
        self.typing_in_progress = False
        
        self.build_admin_panel()
        self.build_video_area()
        
        self.hide_admin_panel()
        
    def build_admin_panel(self):
        self.admin_panel = customtkinter.CTkFrame(self.parent, fg_color="#222222", corner_radius=0)
        
        # Formulario Añadir Cámara
        form_frame = customtkinter.CTkFrame(self.admin_panel, fg_color="transparent")
        form_frame.pack(side="left", padx=20, pady=10, fill="y")
        
        customtkinter.CTkLabel(form_frame, text="✚ Añadir Cámara", font=("Consolas", 14, "bold"), text_color="#00d9ff").pack(anchor="w")
        
        customtkinter.CTkLabel(form_frame, text="Nombre", font=("Consolas", 11)).pack(anchor="w", pady=(5,0))
        self.entry_nombre = customtkinter.CTkEntry(form_frame, placeholder_text="Ej: Cámara Entrada Norte", width=200)
        self.entry_nombre.pack(anchor="w")
        self.entry_nombre.bind("<KeyRelease>", self.on_user_typing)
        
        customtkinter.CTkLabel(form_frame, text="URL Endpoint", font=("Consolas", 11)).pack(anchor="w", pady=(5,0))
        self.entry_url = customtkinter.CTkEntry(form_frame, placeholder_text="rtsp://192.168.1.64:554/stream1", width=300)
        self.entry_url.pack(anchor="w")
        self.entry_url.bind("<KeyRelease>", self.on_user_typing)
        
        self.btn_guardar = customtkinter.CTkButton(form_frame, text="💾 Guardar Cámara", fg_color="#10b981", hover_color="#059669", command=self.agregar_camara)
        self.btn_guardar.pack(anchor="w", pady=10)
        
        # Lista de Cámaras (Eliminar/Seleccionar)
        list_frame = customtkinter.CTkFrame(self.admin_panel, fg_color="transparent")
        list_frame.pack(side="right", padx=20, pady=10, fill="both", expand=True)
        
        self.lbl_count = customtkinter.CTkLabel(list_frame, text="📹 CCTV RED: 0 ACTIVOS", font=("Consolas", 14, "bold"), text_color="#00d9ff")
        self.lbl_count.pack(anchor="ne")
        
        self.cam_combo = customtkinter.CTkComboBox(list_frame, values=["Seleccione una cámara..."], width=250, command=self.seleccionar_camara)
        self.cam_combo.pack(anchor="ne", pady=10)
        
        self.btn_eliminar = customtkinter.CTkButton(list_frame, text="🗑 Eliminar Cámara", fg_color="#e11d48", hover_color="#be123c", command=self.eliminar_camara)
        self.btn_eliminar.pack(anchor="ne")
        
    def build_video_area(self):
        self.video_container = customtkinter.CTkFrame(self.parent, fg_color="#0f0f0f", corner_radius=0)
        self.video_container.grid(row=1, column=0, sticky="nsew")
        
        self.video_label = customtkinter.CTkLabel(self.video_container, text="No hay streams de videovigilancia configurados.\nSeleccione una cámara o expanda el panel superior.", text_color="#555555", font=("Consolas", 14))
        self.video_label.pack(expand=True, fill="both")
        
        # Overlay Toggle Button
        self.btn_toggle_panel = customtkinter.CTkButton(
            self.video_container, text="▼ Panel CCTV ▼", width=120, height=24,
            command=self.toggle_admin_panel
        )
        self.btn_toggle_panel.place(relx=0.5, rely=0.01, anchor="n")
        self.btn_toggle_panel.lift()
        
        # Controles superpuestos (Ocultos por defecto)
        self.controls_frame = customtkinter.CTkFrame(self.video_container, fg_color="#222222", bg_color="transparent", corner_radius=8)
        self.btn_captura = customtkinter.CTkButton(self.controls_frame, text="📸 Capturar", width=100, command=self.tomar_captura)
        self.btn_captura.pack(side="left", padx=5, pady=5)
        
        self.btn_grabar = customtkinter.CTkButton(self.controls_frame, text="⏺ Grabar", width=100, fg_color="#e11d48", hover_color="#be123c", command=self.toggle_grabacion)
        self.btn_grabar.pack(side="left", padx=5, pady=5)
        
    def on_user_typing(self, event):
        self.typing_in_progress = True
        self.reset_auto_hide_timer()
        
    def reset_auto_hide_timer(self):
        if self.panel_timeout_id:
            self.parent.after_cancel(self.panel_timeout_id)
        self.panel_timeout_id = self.parent.after(4000, self.auto_hide_check)
        
    def auto_hide_check(self):
        if not self.typing_in_progress and self.panel_visible:
            self.hide_admin_panel()
        self.typing_in_progress = False # reset state for next check
        if self.panel_visible:
            self.reset_auto_hide_timer()

    def toggle_admin_panel(self):
        if self.panel_visible:
            self.hide_admin_panel()
        else:
            self.show_admin_panel()

    def show_admin_panel(self):
        self.admin_panel.grid(row=0, column=0, sticky="ew")
        self.btn_toggle_panel.configure(text="▲ Ocultar Panel ▲")
        self.panel_visible = True
        self.typing_in_progress = False
        self.reset_auto_hide_timer()
        
    def hide_admin_panel(self):
        self.admin_panel.grid_remove()
        self.btn_toggle_panel.configure(text="▼ Panel CCTV ▼")
        self.panel_visible = False
        if self.panel_timeout_id:
            self.parent.after_cancel(self.panel_timeout_id)
            self.panel_timeout_id = None
            
    def agregar_camara(self):
        nombre = self.entry_nombre.get()
        url = self.entry_url.get()
        if nombre and url:
            self.cameras.append({"nombre": nombre, "url": url})
            self.entry_nombre.delete(0, "end")
            self.entry_url.delete(0, "end")
            self.typing_in_progress = False
            self.actualizar_lista_camaras()
            if hasattr(self.master_app, "send_alert"):
                self.master_app.send_alert(f"Cámara {nombre} añadida", "green")
            
    def eliminar_camara(self):
        seleccion = self.cam_combo.get()
        for i, c in enumerate(self.cameras):
            if c["nombre"] == seleccion:
                del self.cameras[i]
                if self.active_camera_index == i:
                    self.detener_stream()
                self.actualizar_lista_camaras()
                if hasattr(self.master_app, "send_alert"):
                    self.master_app.send_alert(f"Cámara eliminada", "red")
                break
                
    def actualizar_lista_camaras(self):
        self.lbl_count.configure(text=f"📹 CCTV RED: {len(self.cameras)} ACTIVOS")
        if self.cameras:
            nombres = [c["nombre"] for c in self.cameras]
            self.cam_combo.configure(values=nombres)
            self.cam_combo.set(nombres[-1])
        else:
            self.cam_combo.configure(values=["Seleccione una cámara..."])
            self.cam_combo.set("Seleccione una cámara...")
            
    def seleccionar_camara(self, value):
        for i, c in enumerate(self.cameras):
            if c["nombre"] == value:
                self.iniciar_stream(i)
                break
                
    def iniciar_stream(self, index):
        self.detener_stream()
        self.active_camera_index = index
        self.is_playing = True
        self.controls_frame.place(relx=0.5, rely=0.9, anchor="s")
        self.capture_thread = threading.Thread(target=self._stream_loop, args=(self.cameras[index]["url"],), daemon=True)
        self.capture_thread.start()
        
    def detener_stream(self):
        self.is_playing = False
        self.active_camera_index = -1
        self.controls_frame.place_forget()
        self.video_label.configure(image="", text="Conexión cerrada.")
        if self.is_recording:
            self.toggle_grabacion()
            
    def _stream_loop(self, url):
        cap = cv2.VideoCapture(url)
        # Optimize for latency if using RTSP
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        while self.is_playing and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                if self.is_recording and self.video_writer:
                    self.video_writer.write(frame)
                    
                # Convert to PIL and Tkinter format
                # Resize keeping aspect ratio for a fixed maximum size (e.g. 800x600)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                
                # Resize dynamically based on label size (simplification: fixed for now)
                image = image.resize((800, 450), Image.LANCZOS)
                
                imgtk = ImageTk.PhotoImage(image=image)
                
                # Update UI in main thread safely
                self.parent.after(0, self._update_video_label, imgtk, frame)
            else:
                break
            time.sleep(0.03) # ~30 fps limit to save CPU
            
        cap.release()
        if self.is_playing:
            self.parent.after(0, lambda: self.video_label.configure(image="", text="Conexión perdida o stream inaccesible."))
            
    def _update_video_label(self, imgtk, raw_frame):
        if self.is_playing:
            self.video_label.configure(image=imgtk, text="")
            self.video_label.image = imgtk
            self.last_raw_frame = raw_frame # store for snapshot
            
    def tomar_captura(self):
        if hasattr(self, 'last_raw_frame') and self.active_camera_index != -1:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            cam_name = self.cameras[self.active_camera_index]["nombre"].replace(" ", "_")
            filename = f"captura_{cam_name}_{timestamp}.jpg"
            cv2.imwrite(filename, self.last_raw_frame)
            if hasattr(self.master_app, "send_alert"):
                self.master_app.send_alert(f"Captura guardada: {filename}", "green")
            
    def toggle_grabacion(self):
        if not self.is_recording:
            if hasattr(self, 'last_raw_frame') and self.active_camera_index != -1:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                cam_name = self.cameras[self.active_camera_index]["nombre"].replace(" ", "_")
                filename = f"grabacion_{cam_name}_{timestamp}.avi"
                
                height, width, _ = self.last_raw_frame.shape
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
                
                self.is_recording = True
                self.btn_grabar.configure(text="⏹ Detener Rec", fg_color="#9f1239")
                if hasattr(self.master_app, "send_alert"):
                    self.master_app.send_alert(f"Grabación iniciada: {filename}", "green")
        else:
            self.is_recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            self.btn_grabar.configure(text="⏺ Grabar", fg_color="#e11d48")
            if hasattr(self.master_app, "send_alert"):
                self.master_app.send_alert("Grabación detenida.", "green")
