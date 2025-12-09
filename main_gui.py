import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import webbrowser
import os
import subprocess
import json
from pathlib import Path
import ttkbootstrap as tb # Import as tb to avoid conflict
from ttkbootstrap import Style
from datetime import datetime

# Importamos logica de negocio
from src.scanner import scan_directory
from src.mover import move_media_safe, STATUS_SUCCESS, STATUS_SKIPPED, STATUS_ERROR, STATUS_DUPLICATE
from src.deduplicator import scan_and_move_duplicates

class OrganizerApp(tb.Window): # Extend tb.Window instead of ttk.Window
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Organizador Multimedia Pro v2.0")
        self.geometry("750x650")
        self.resizable(False, False)
        
        # Estilo para botones TK estándar
        # Estilo para botones TK estándar
        self.style.configure('TButton', font=('Segoe UI', 9, 'bold'), padding=(10, 10))

        # --- Variables (Organizador) ---
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.dry_run = tk.BooleanVar(value=False)
        self.is_running = False
        self.last_log_file = None
        
        # --- Variables (Exclusión de Carpetas) ---
        self.excluded_folders = []  # Lista de rutas excluidas
        self.persist_exclusions = tk.BooleanVar(value=False)
        self.config_file = Path("excluded_folders.json")

        # --- Variables (Duplicados) ---
        self.dup_target_path = tk.StringVar()
        self.is_dup_running = False

        # Cola de mensajes para thread-safety
        self.log_queue = queue.Queue()
        
        self._build_ui()
        self.load_excluded_folders()
        self.check_queue()

    def _build_ui(self):
        # Contenedor principal con pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Organizador
        self.tab_organizer = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_organizer, text=" 📂 Organizador Multimedia ")
        self._build_organizer_tab(self.tab_organizer)

        # Tab 2: Limpiador de Duplicados
        self.tab_duplicates = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_duplicates, text=" 🕵️ Buscador de Duplicados ")
        self._build_duplicates_tab(self.tab_duplicates)

        # Footer común
        footer_frame = ttk.Frame(self)
        footer_frame.pack(side='bottom', fill=tk.X, padx=10, pady=5)
        ttk.Label(footer_frame, text="slider66 © 2025 OrdenaFotos Pro | v2.0", font=("Segoe UI", 8)).pack(side=tk.RIGHT)
        link = ttk.Label(footer_frame, text="Ayuda / Documentación", font=("Segoe UI", 8, "underline"), cursor="hand2")
        link.pack(side=tk.LEFT)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/slider66/OrdenaFotos"))

    def _build_organizer_tab(self, parent):
        container = ttk.Frame(parent, padding=15)
        container.pack(fill='both', expand=True)

        # --- SECCIÓN 1: Selección de Rutas ---
        lbl_frame = ttk.LabelFrame(container, text=" Configuración de Rutas ", padding=10)
        lbl_frame.pack(fill=tk.X, pady=(0, 10))

        # Origen
        ttk.Label(lbl_frame, text="Origen (Fotos desordenadas):").pack(anchor=tk.W)
        src_row = ttk.Frame(lbl_frame)
        src_row.pack(fill=tk.X, pady=5)
        ttk.Entry(src_row, textvariable=self.source_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(src_row, text="Examinar", command=self.browse_source, bootstyle="secondary").pack(side=tk.RIGHT)

        # Destino
        ttk.Label(lbl_frame, text="Destino (Carpeta Organizada):").pack(anchor=tk.W, pady=(10, 0))
        dest_row = ttk.Frame(lbl_frame)
        dest_row.pack(fill=tk.X, pady=5)
        ttk.Entry(dest_row, textvariable=self.dest_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dest_row, text="Examinar", command=self.browse_dest, bootstyle="secondary").pack(side=tk.RIGHT)
        
        # --- SECCIÓN: Carpetas Excluidas ---
        exc_frame = ttk.LabelFrame(container, text=" Carpetas Excluidas del Escaneo ", padding=10)
        exc_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Checkbox para persistencia
        persist_check = ttk.Checkbutton(
            exc_frame, 
            text="Guardar exclusiones entre sesiones",
            variable=self.persist_exclusions,
            command=self.on_persist_toggle,
            bootstyle="round-toggle"
        )
        persist_check.pack(anchor=tk.W, pady=(0, 5))
        
        # Frame para listbox y botones
        exc_content = ttk.Frame(exc_frame)
        exc_content.pack(fill=tk.BOTH, expand=True)
        
        # Listbox con scrollbar
        list_frame = ttk.Frame(exc_content)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.excluded_listbox = tk.Listbox(list_frame, height=4, selectmode=tk.EXTENDED, font=("Segoe UI", 9))
        self.excluded_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        exc_scrollbar = ttk.Scrollbar(list_frame, command=self.excluded_listbox.yview)
        exc_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.excluded_listbox['yscrollcommand'] = exc_scrollbar.set
        
        # Botones
        btn_container = ttk.Frame(exc_content)
        btn_container.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(
            btn_container,
            text="➕ Añadir",
            command=self.add_excluded_folder,
            bootstyle="success"
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            btn_container,
            text="➖ Eliminar",
            command=self.remove_excluded_folders,
            bootstyle="danger"
        ).pack(fill=tk.X, pady=2)

        # --- SECCIÓN 2: Opciones y Progreso ---
        opts_frame = ttk.Frame(container)
        opts_frame.pack(fill=tk.X, pady=10)
        
        ttk.Checkbutton(opts_frame, text="Modo Simulación (Dry Run) - No mueve archivos", variable=self.dry_run, bootstyle="round-toggle").pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(container, mode='indeterminate', bootstyle="success-striped")
        self.progress_bar.pack(fill=tk.X, pady=(0, 15))

        # --- SECCIÓN 3: Botones de Acción ---
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X)

        self.btn_start = tk.Button(btn_frame, text="INICIAR ORGANIZACIÓN", command=self.start_process, 
                                   bg="#00bc8c", fg="white", font=("Segoe UI", 10, "bold"), 
                                   height=2, width=25, relief="flat", cursor="hand2")
        self.btn_start.pack(side=tk.RIGHT, padx=5)

        self.btn_stop = tk.Button(btn_frame, text="DETENER", command=self.stop_process, state='disabled',
                                  bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
                                  height=2, width=15, relief="flat", cursor="hand2")
        self.btn_stop.pack(side=tk.RIGHT, padx=5)

        self.btn_open_log = tk.Button(btn_frame, text="ABRIR LOG", command=self.open_last_log, state='disabled',
                                      bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
                                      height=2, width=15, relief="flat", cursor="hand2")
        self.btn_open_log.pack(side=tk.LEFT, padx=5)

        # --- SECCIÓN 4: Log ---
        log_frame = ttk.LabelFrame(container, text=" Registro de Actividad ", padding=5)
        log_frame.pack(fill='both', expand=True, pady=(15, 0))

        self.log_text = tk.Text(log_frame, height=8, state='disabled', font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.log_text['yscrollcommand'] = scrollbar.set

    def _build_duplicates_tab(self, parent):
        container = ttk.Frame(parent, padding=15)
        container.pack(fill='both', expand=True)

        ttk.Label(container, text="Esta herramienta busca archivos idénticos (mismo contenido) en una carpeta y mueve los duplicados a '_DUPLICADOS'.", wraplength=700).pack(pady=(0, 20))

        # Selección de Carpeta Única
        lbl_frame = ttk.LabelFrame(container, text=" Carpeta a Analizar ", padding=10)
        lbl_frame.pack(fill=tk.X, pady=(0, 20))

        row = ttk.Frame(lbl_frame)
        row.pack(fill=tk.X)
        ttk.Entry(row, textvariable=self.dup_target_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(row, text="Examinar", command=self.browse_dup_target, bootstyle="secondary").pack(side=tk.RIGHT)

        # Botón Acción
        self.btn_find_dups = tk.Button(container, text="BUSCAR Y MOVER DUPLICADOS", command=self.start_deduplication,
                                       bg="#f39c12", fg="white", font=("Segoe UI", 10, "bold"),
                                       height=2, width=30, relief="flat", cursor="hand2")
        self.btn_find_dups.pack(pady=10)

        self.dup_progress = ttk.Progressbar(container, mode='indeterminate', bootstyle="warning-striped")
        self.dup_progress.pack(fill=tk.X, pady=10)

        # Log Específico
        log_frame = ttk.LabelFrame(container, text=" Resultados de Búsqueda ", padding=5)
        log_frame.pack(fill='both', expand=True)

        self.dup_log_text = tk.Text(log_frame, height=10, state='disabled', font=("Consolas", 9))
        self.dup_log_text.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar = ttk.Scrollbar(log_frame, command=self.dup_log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.dup_log_text['yscrollcommand'] = scrollbar.set

    # --- Funciones GUI Genéricas ---
    def log_message(self, message, area='organizer'):
        self.log_queue.put((message, area))

    def check_queue(self):
        while not self.log_queue.empty():
            msg, area = self.log_queue.get()
            target_text = self.log_text if area == 'organizer' else self.dup_log_text
            
            target_text.config(state='normal')
            target_text.insert(tk.END, msg + "\n")
            target_text.see(tk.END)
            target_text.config(state='disabled')
        
        self.after(100, self.check_queue)

    def browse_source(self):
        path = filedialog.askdirectory()
        if path: self.source_path.set(path)

    def browse_dest(self):
        path = filedialog.askdirectory()
        if path: self.dest_path.set(path)

    def browse_dup_target(self):
        path = filedialog.askdirectory()
        if path: self.dup_target_path.set(path)

    # --- Lógica Organizador (Tab 1) ---
    def start_process(self):
        src = self.source_path.get()
        dest = self.dest_path.get()
        
        if not src or not dest:
            messagebox.showerror("Error", "Debes seleccionar ambas rutas.")
            return

        self.is_running = True
        self.btn_start.config(state='disabled', bg="#95a5a6") # Gris deshabilitado
        self.btn_stop.config(state='normal', bg="#e74c3c")
        self.btn_open_log.config(state='disabled', bg="#95a5a6")
        self.progress_bar.start(10)
        
        # Limpiar log visual
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

        threading.Thread(target=self.run_organization, args=(src, dest), daemon=True).start()

    def stop_process(self):
        self.is_running = False
        self.log_message("!!! DETENIENDO PROCESO... Espera a que termine la tarea actual.", 'organizer')
        self.btn_stop.config(state='disabled', bg="#95a5a6")

    def open_last_log(self):
        if self.last_log_file and os.path.exists(self.last_log_file):
            try:
                if os.name == 'nt':
                     os.startfile(self.last_log_file)
                else:
                    subprocess.call(('xdg-open', self.last_log_file))
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el log: {e}")
        else:
            messagebox.showinfo("Info", "No hay log disponible reciente.")

    def run_organization(self, src_path, dest_path):
        self.log_message(f"--- Iniciando {'SIMULACIÓN' if self.dry_run.get() else 'PROCESO'} ---", 'organizer')
        self.log_message(f"Origen: {src_path}", 'organizer')
        self.log_message(f"Destino: {dest_path}", 'organizer')
        
        # Preparar Log File
        log_filename = f"operaciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path = Path(dest_path) / log_filename
        self.last_log_file = str(log_path)

        if not self.dry_run.get():
             try:
                 Path(dest_path).mkdir(parents=True, exist_ok=True)
             except Exception as e:
                 self.log_message(f"Error creando destino: {e}", 'organizer')
                 self.stop_ui_loading()
                 return

        try:
             with open(log_path, 'w', encoding='utf-8') as log_file:
                def log_both(msg):
                    self.log_message(msg, 'organizer')
                    log_file.write(msg + "\n")
                    log_file.flush()

                total_processed = 0
                errors = 0
                
                for media_group in scan_directory(Path(src_path), set(self.excluded_folders)):
                    if not self.is_running:
                        log_both(">>> PROCESO DETENIDO POR EL USUARIO <<<")
                        break
                    
                    try:
                        result = move_media_safe(media_group, Path(dest_path), duplicate_action='ask', dry_run=self.dry_run.get())
                        
                        icon = "✅"
                        if result.status == STATUS_SKIPPED: icon = "⏭️"
                        if result.status == STATUS_DUPLICATE: icon = "👯"
                        if result.status == STATUS_ERROR: 
                            icon = "❌"
                            errors += 1
                        
                        log_both(f"{icon} [{media_group.main_file.name}]: {result.message}")
                        total_processed += 1
                        
                    except Exception as e:
                        log_both(f"❌ Error inesperado con {media_group}: {e}")
                        errors += 1
                
                log_both(f"--- FINALIZADO. Total: {total_processed} | Errores: {errors} ---")
                
                if not self.dry_run.get() and self.is_running:
                    log_both("Limpiando carpetas vacías en origen...")
                    self.cleanup_empty_folders(Path(src_path))
                    log_both("Limpieza completada.")

        except Exception as e:
            self.log_message(f"ERROR CRITICO: {str(e)}", 'organizer')
        
        finally:
            self.stop_ui_loading()
            self.btn_open_log.config(state='normal', bg="#3498db")

    def stop_ui_loading(self):
        self.is_running = False
        self.progress_bar.stop()
        self.btn_start.config(state='normal', bg="#00bc8c")
        self.btn_stop.config(state='disabled', bg="#e74c3c")

    def cleanup_empty_folders(self, path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in dirs:
                try:
                    p = Path(root) / name
                    if not any(p.iterdir()):
                        p.rmdir()
                except:
                    pass
    
    # --- Funciones de Exclusión de Carpetas ---
    def load_excluded_folders(self):
        """Carga las carpetas excluidas desde el archivo JSON si existe y está habilitado."""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Solo cargar si la persistencia estaba habilitada
            if data.get('persist_exclusions', False):
                self.persist_exclusions.set(True)
                self.excluded_folders = data.get('excluded_folders', [])
                self.update_excluded_listbox()
        except Exception as e:
            print(f"Error cargando exclusiones: {e}")
    
    def save_excluded_folders(self):
        """Guarda las carpetas excluidas al archivo JSON si la persistencia está habilitada."""
        if not self.persist_exclusions.get():
            # Si no está habilitada la persistencia, eliminar el archivo si existe
            if self.config_file.exists():
                try:
                    self.config_file.unlink()
                except:
                    pass
            return
        
        try:
            data = {
                'persist_exclusions': True,
                'excluded_folders': self.excluded_folders
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando exclusiones: {e}")
    
    def add_excluded_folder(self):
        """Abre diálogo para añadir una carpeta a excluir."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta a excluir")
        if folder and folder not in self.excluded_folders:
            self.excluded_folders.append(folder)
            self.update_excluded_listbox()
            self.save_excluded_folders()
    
    def remove_excluded_folders(self):
        """Elimina las carpetas seleccionadas de la lista de exclusiones."""
        selected_indices = self.excluded_listbox.curselection()
        if not selected_indices:
            return
        
        # Eliminar de atrás hacia adelante para no alterar índices
        for index in reversed(selected_indices):
            del self.excluded_folders[index]
        
        self.update_excluded_listbox()
        self.save_excluded_folders()
    
    def update_excluded_listbox(self):
        """Actualiza la listbox con las carpetas excluidas actuales."""
        self.excluded_listbox.delete(0, tk.END)
        for folder in self.excluded_folders:
            self.excluded_listbox.insert(tk.END, folder)
    
    def on_persist_toggle(self):
        """Maneja el cambio del checkbox de persistencia."""
        self.save_excluded_folders()

    # --- Lógica Duplicados (Tab 2) ---
    def start_deduplication(self):
        target = self.dup_target_path.get()
        if not target:
            messagebox.showerror("Error", "Selecciona una carpeta para analizar.")
            return

        self.is_dup_running = True
        self.btn_find_dups.config(state='disabled', bg="#95a5a6")
        self.dup_progress.start(10)
        
        # Limpiar log visual
        self.dup_log_text.config(state='normal')
        self.dup_log_text.delete(1.0, tk.END)
        self.dup_log_text.config(state='disabled')
        
        threading.Thread(target=self.run_deduplication, args=(target,), daemon=True).start()

    def run_deduplication(self, target_path):
        self.log_message(f"--- Iniciando Búsqueda de Duplicados en: {target_path} ---", 'duplicates')
        
        try:
            for msg in scan_and_move_duplicates(target_path):
                 self.log_message(msg, 'duplicates')
        except Exception as e:
             self.log_message(f"ERROR: {str(e)}", 'duplicates')
        finally:
            self.is_dup_running = False
            self.dup_progress.stop()
            self.btn_find_dups.config(state='normal', bg="#f39c12")

if __name__ == "__main__":
    app = OrganizerApp()
    app.mainloop()
