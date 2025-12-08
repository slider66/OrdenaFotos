import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
from pathlib import Path
import time

from src.scanner import scan_directory
from src.mover import move_media_safe, STATUS_SUCCESS, STATUS_DUPLICATE, STATUS_ERROR, STATUS_SKIPPED
from src.cleaner import clean_empty_directories

class OrganizerApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="superhero") # Tema moderno oscuro
        self.title("Organizador Multimedia Pro")
        self.geometry("700x550")
        self.resizable(False, False)

        # Variables de estado
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.is_running = False
        self.stop_event = threading.Event()

        self._build_ui()

    def _build_ui(self):
        # Contenedor Principal
        main_container = ttk.Frame(self, padding=20)
        main_container.pack(fill=BOTH, expand=True)
        
        # Título Header
        header_lbl = ttk.Label(main_container, text="Organizador de Fotos & Video", font=("Helvetica", 16, "bold"), bootstyle="primary")
        header_lbl.pack(pady=(0, 20))

        # --- SECCIÓN 1: Selección de Rutas ---
        rutas_frame = ttk.Labelframe(main_container, text=" Configuración de Carpetas ", padding=15, bootstyle="info")
        rutas_frame.pack(fill=X, pady=5)

        # Origen
        ttk.Label(rutas_frame, text="Carpeta Origen (Cámara/Teléfono):", font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=(0,5))
        src_entry = ttk.Entry(rutas_frame, textvariable=self.source_path, width=45)
        src_entry.grid(row=1, column=0, padx=(0, 10), pady=(0, 15))
        ttk.Button(rutas_frame, text="📂 Buscar", command=self.select_source, bootstyle="secondary-outline").grid(row=1, column=1, pady=(0, 15))

        # Destino
        ttk.Label(rutas_frame, text="Carpeta Destino (Biblioteca Organizada):", font=("Helvetica", 10)).grid(row=2, column=0, sticky="w", pady=(0,5))
        dst_entry = ttk.Entry(rutas_frame, textvariable=self.dest_path, width=45)
        dst_entry.grid(row=3, column=0, padx=(0, 10))
        ttk.Button(rutas_frame, text="📂 Buscar", command=self.select_dest, bootstyle="secondary-outline").grid(row=3, column=1)

        # --- SECCIÓN 2: Panel de Progreso y Logs ---
        progress_frame = ttk.Labelframe(main_container, text=" Estado del Proceso ", padding=15, bootstyle="success")
        progress_frame.pack(fill=BOTH, expand=True, pady=15)

        self.log_text = tk.Text(progress_frame, height=8, state='disabled', font=("Consolas", 9), bg="#2b3e50", fg="white", relief="flat")
        self.log_text.pack(fill=BOTH, expand=True, side=LEFT)
        
        # Scrollvar para logs
        scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=self.log_text.yview, bootstyle="success-round")
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.progress_bar = ttk.Progressbar(main_container, mode='indeterminate', bootstyle="success-striped")
        self.progress_bar.pack(fill=X, pady=(0, 15))

        # --- SECCIÓN 3: Botones de Acción ---
        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(fill=X)

        self.btn_start = ttk.Button(btn_frame, text="⚡ INICIAR ORGANIZACIÓN", command=self.start_process, bootstyle="success", width=25)
        self.btn_start.pack(side=RIGHT, padx=5)

        self.btn_stop = ttk.Button(btn_frame, text="🛑 Detener", command=self.stop_process, state='disabled', bootstyle="danger-outline")
        self.btn_stop.pack(side=RIGHT, padx=5)

        # Footer
        footer_lbl = ttk.Label(main_container, text="v1.0.0 | OrdenaFotos Local", font=("Segoe UI", 8), bootstyle="secondary")
        footer_lbl.pack(side=LEFT, pady=5)

    def select_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_path.set(path)

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_path.set(path)

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_process(self):
        src = self.source_path.get()
        dst = self.dest_path.get()

        if not src or not dst:
            messagebox.showwarning("Faltan rutas", "Por favor selecciona origen y destino.")
            return

        if not Path(src).exists():
            messagebox.showerror("Error", "La ruta de origen no existe.")
            return

        self.is_running = True
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.source_path_entry_widget = None # TODO: Bloquear entry widgets si fuera necesario
        self.stop_event.clear()
        self.progress_bar.start(10)

        # Ejecutar en hilo separado para no congelar la UI
        threading.Thread(target=self.run_organization_logic, args=(Path(src), Path(dst)), daemon=True).start()

    def stop_process(self):
        if self.is_running:
            self.stop_event.set()
            self.log(">>> Deteniendo proceso... espere...")

    def run_organization_logic(self, src: Path, dst: Path):
        self.log(f"--- Iniciando escaneo en: {src} ---")
        
        count_success = 0
        count_errors = 0
        count_skipped = 0
        
        try:
            # 1. Escaneo
            media_files = list(scan_directory(src))
            total_files = len(media_files)
            self.log(f"Archivos multimedia encontrados: {total_files}")
            
            self.progress_bar.stop()
            self.progress_bar['mode'] = 'determinate'
            self.progress_bar['maximum'] = total_files
            self.progress_bar['value'] = 0

            # 2. Procesamiento
            for i, media_group in enumerate(media_files):
                if self.stop_event.is_set():
                    self.log("!!! Proceso detenido por usuario !!!")
                    break

                # Lógica de Movimiento
                # Por ahora acción de duplicado es 'ask', pero como es CLI/Hilo GUI, 
                # implementaremos un manejo simplificado o popup sincrono (cuidado con thread safety).
                # Para la v1 Usaremos 'rename' automático si es falso duplicado, y 'skip' si es true duplicate para no bloquear.
                # O mejor, usamos ask_duplicate_action via invoke si tkinter thread safe.
                
                # Intento de mover con acción por defecto SKIP para duplicados exactos para evitar spam de popups en MVP
                # En una v2 se puede hacer un queue para preguntar a la UI.
                
                result = move_media_safe(media_group, dst, duplicate_action='skip') # TODO: Hacer configurable en UI

                # Procesar Resultado
                if result.status == STATUS_DUPLICATE:
                    # Si 'skip' fallbackeo a mostrarlo
                    self.log(f"[DUP] {media_group.main_file.name} -> Duplicado exacto omitido.")
                    count_skipped += 1
                
                elif result.status == STATUS_SKIPPED:
                    self.log(f"[SKIP] {media_group.main_file.name} -> {result.message}")
                    count_skipped += 1

                elif result.status == STATUS_ERROR:
                    self.log(f"[ERR] {media_group.main_file.name} -> {result.message}")
                    count_errors += 1
                
                else: # SUCCESS
                    # self.log(f"[OK] {media_group.main_file.name}") # Verbose off para velocidad
                    count_success += 1

                # Actualizar cada 5 archivos para no saturar UI
                if i % 5 == 0:
                    self.progress_bar['value'] = i + 1
                    self.update_idletasks()

            # 3. Limpieza
            if not self.stop_event.is_set():
                self.log("--- Limpiando directorios vacíos en origen ---")
                clean_empty_directories(src)
                self.progress_bar['value'] = total_files

            # Resumen
            self.log(f"\n=== FINALIZADO ===")
            self.log(f"Movidos: {count_success}")
            self.log(f"Omitidos/Duplicados: {count_skipped}")
            self.log(f"Errores: {count_errors}")
            
            messagebox.showinfo("Proceso Completado", f"Organización finalizada.\n\nMovidos: {count_success}\nOmitidos: {count_skipped}\nErrores: {count_errors}")

        except Exception as e:
            self.log(f"ERROR FATAL: {e}")
            messagebox.showerror("Error Fatal", str(e))
        
        finally:
            self.is_running = False
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')
            self.progress_bar.stop()
            self.progress_bar['mode'] = 'indeterminate'

if __name__ == "__main__":
    app = OrganizerApp()
    app.mainloop()
