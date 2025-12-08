# Plan de Implementación: Organizador Multimedia Local

Este documento detalla el plan de trabajo para desarrollar la utilidad de organización de fotos y videos descrita en el `README.md`.

## 📦 Fase 1: Configuración y Núcleo (Core Logic)

Objetivo: Establecer el entorno y las funciones base para el manejo de metadatos y hashing.

- [ ] **1.1. Inicialización del Proyecto**

  - Crear estructura de carpetas (`src`, `tests`).
  - Configurar entorno virtual (`venv`) y archivo `requirements.txt`.
  - Dependencias iniciales: `Pillow`, `ExifRead` (si es necesario para RAW/HEIC).

- [ ] **1.2. Módulo de Extracción de Fechas (`date_extractor.py`)**

  - Implementar lógica de prioridad descrita:
    1.  **EXIF/Tags**: Usar `Pillow` y `ExifRead` para obtener fecha de captura original.
    2.  **Sistema de Archivos (Creación)**: Fallback a `os.path.getctime`.
    3.  **Sistema de Archivos (Modificación)**: Fallback a `os.path.getmtime`.
  - Retornar objeto `datetime` para clasificación.

- [ ] **1.3. Módulo de Integridad y Hashing (`integrity.py`)**
  - Implementar función para calcular SHA-256 de un archivo.
  - Crear función de comparación: `check_duplicate(file_a, file_b)` -> bool.

## 🚀 Fase 2: Gestión de Archivos y Movimiento

Objetivo: Implementar la lógica segura de transferencia y soporte de formatos.

- [ ] **2.1. Escáner de Archivos (`scanner.py`)**

  - Función para recorrer recursivamente el directorio de origen.
  - Filtro de extensiones permitidas (Imágenes, Video, RAW) según lista del README.
  - Detección de archivos "Sidecar" (`.aae`, `.xmp`) para asociarlos al archivo principal.

- [ ] **2.2. Motor de Movimiento Seguro (`mover.py`)**

  - Implementar `safe_move(origen, destino_base)`:
    - Calcular ruta destino: `DestinoBase\Año\Mes\Archivo.ext`.
    - **Validación 1**: Si existe archivo en destino con mismo nombre -> Invocar lógica de duplicados.
    - **Validación 2**: Mover archivo (`shutil.move`).
    - **Validación 3**: Verificar existencia y tamaño en destino.
    - **Rollback**: Si falla, alertar y no borrar origen.

- [ ] **2.3. Lógica de Resolución de Conflictos**

  - Manejo interactivo cuando se detecta duplicado (Hash coincidente):
    - Opciones: Sobrescribir, Omitir, Omitir Todos, Eliminar Original.
  - Manejo automático cuando es colisión de nombre pero diferente contenido (Hash diferente):
    - Renombrado automático (ej: `foto_dup_1.jpg`).

- [ ] **2.4. Limpieza Post-Proceso (`cleaner.py`)**
  - Barrido recursivo inverso para eliminar carpetas vacías en la ruta de origen.

## 🖥️ Fase 3: Interfaz de Usuario

Objetivo: Proveer una forma amigable de usar la herramienta.

- [ ] **3.1. Interfaz Gráfica Básica (Tkinter)**
  - Ventana principal para selección de `Ruta Origen` y `Ruta Destino`.
  - Botón "Iniciar Organización".
  - Barra de progreso o log de actividad en pantalla.
  - **Modal de Resolución**: Popup para preguntar al usuario qué hacer en caso de duplicados exactos.

## ✅ Fase 4: Pruebas y Empaquetado

Objetivo: Validar robustez y facilitar distribución.

- [ ] **4.1. Pruebas Unitarias**

  - Tests para extracción de fechas (casos con/sin EXIF).
  - Tests de hashing y detección de duplicados.
  - Simulación de movimiento con validación de tamaño.

- [ ] **4.2. Validación Manual**
  - Prueba con set de datos real (fotos HEIC, RAW, videos).
