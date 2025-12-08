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
        self.dry_run = tk.BooleanVar(value=False) # Variable para Checkbox
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
        
        # Checkbox Simulación
        chk_dry = ttk.Checkbutton(rutas_frame, text="Modo Simulación (No mover archivos)", variable=self.dry_run, bootstyle="warning-round-toggle")
        chk_dry.grid(row=4, column=0, sticky="w", pady=(15, 0))

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

        self.btn_open_log = ttk.Button(btn_frame, text="📄 Abrir Log", command=self.open_last_log, state='disabled', bootstyle="info-outline")
        self.btn_open_log.pack(side=LEFT, padx=5)

        # Footer
        footer_lbl = ttk.Label(main_container, text="v1.1.0 | OrdenaFotos Local", font=("Segoe UI", 8), bootstyle="secondary")
        footer_lbl.pack(side=LEFT, pady=5)

    def select_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_path.set(path)

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_path.set(path)

    def open_last_log(self):
        if hasattr(self, 'last_log_path') and self.last_log_path.exists():
            import os
            try:
                os.startfile(self.last_log_path)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el log: {e}")
        else:
             messagebox.showinfo("Info", "No hay log reciente disponible.")

    def log(self, message):
        # 1. UI Log
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
        # 2. File Log (Si tenemos un descriptor de archivo abierto)
        if hasattr(self, 'log_file'):
            try:
                timestamp = time.strftime("%H:%M:%S")
                self.log_file.write(f"[{timestamp}] {message}\n")
                self.log_file.flush()
            except Exception:
                pass

    def start_process(self):
        src = self.source_path.get()
        dst = self.dest_path.get()
        is_dry_run = self.dry_run.get()

        if not src or not dst:
            messagebox.showwarning("Faltan rutas", "Por favor selecciona origen y destino.")
            return

        if not Path(src).exists():
            messagebox.showerror("Error", "La ruta de origen no existe.")
            return

        self.is_running = True
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.btn_open_log.config(state='disabled')
        self.stop_event.clear()
        self.progress_bar.start(10)

        # Ejecutar en hilo separado para no congelar la UI
        threading.Thread(target=self.run_organization_logic, args=(Path(src), Path(dst), is_dry_run), daemon=True).start()

    def stop_process(self):
        if self.is_running:
            self.stop_event.set()
            self.log(">>> Deteniendo proceso... espere...")

    def run_organization_logic(self, src: Path, dst: Path, dry_run: bool):
        # Iniciar Log Persistente
        try:
            log_filename = f"operaciones_{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"
            if dry_run: log_filename = "SIMULATION_" + log_filename
            
            if not dst.exists() and not dry_run:
                dst.mkdir(parents=True, exist_ok=True)
            
            log_path = dst / log_filename
            
            if not dst.exists() and dry_run:
                log_path = src / log_filename

            self.log_file = open(log_path, "w", encoding="utf-8")
            self.last_log_path = log_path # Guardar referencia para abrir después
        except Exception as e:
            self.log(f"Advertencia: No se pudo crear archivo de log: {e}")

        self.log(f"--- Iniciando escaneo en: {src} ---")
        if dry_run:
            self.log("=== MODO SIMULACIÓN: NO SE MOVERÁN ARCHIVOS ===")
        
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
                result = move_media_safe(media_group, dst, duplicate_action='skip', dry_run=dry_run)

                # Procesar Resultado
                if result.status == STATUS_DUPLICATE:
                    self.log(f"[DUP] {media_group.main_file.name} -> Duplicado exacto omitido.")
                    count_skipped += 1
                
                elif result.status == STATUS_SKIPPED:
                    self.log(f"[SKIP] {media_group.main_file.name} -> {result.message}")
                    count_skipped += 1

                elif result.status == STATUS_ERROR:
                    self.log(f"[ERR] {media_group.main_file.name} -> {result.message}")
                    count_errors += 1
                
                else: # SUCCESS
                    if dry_run:
                        self.log(f"[SIMULADO] Mover {media_group.main_file.name} -> {result.destination}")
                    count_success += 1

                # Actualizar cada 5 archivos para no saturar UI
                if i % 5 == 0:
                    self.progress_bar['value'] = i + 1
                    self.update_idletasks()

            # 3. Limpieza
            if not self.stop_event.is_set():
                if not dry_run:
                    self.log("--- Limpiando directorios vacíos en origen ---")
                    clean_empty_directories(src)
                else:
                    self.log("--- Limpieza omitida (Dry Run) ---")
                    
                self.progress_bar['value'] = total_files

            # Resumen
            self.log(f"\n=== FINALIZADO ===")
            self.log(f"Procesados: {count_success}")
            self.log(f"Omitidos/Duplicados: {count_skipped}")
            self.log(f"Errores: {count_errors}")
            if hasattr(self, 'log_file'): 
                self.log(f"Log guardado en: {log_path}")
            
            msg_title = "Proceso Completado"
            if dry_run: msg_title += " (Simulación)"
            
            messagebox.showinfo(msg_title, f"Finalizado.\n\nExitosos: {count_success}\nOmitidos: {count_skipped}\nErrores: {count_errors}\n\nLog: {log_path.name}")

        except Exception as e:
            self.log(f"ERROR FATAL: {e}")
            messagebox.showerror("Error Fatal", str(e))
        
        finally:
            self.is_running = False
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')
            self.btn_open_log.config(state='normal') # Habilitar botón Log
            self.progress_bar.stop()
            self.progress_bar['mode'] = 'indeterminate'
            if hasattr(self, 'log_file'):
                self.log_file.close()

if __name__ == "__main__":
    app = OrganizerApp()
    app.mainloop()
