# 📂 Utilidad de Organización Multimedia Local

> 🇺🇸 [Read in English](README.md)

## 🎯 Objetivo del Proyecto

Crear una aplicación de escritorio local, sencilla y robusta, diseñada para automatizar la organización de archivos multimedia. Incluye dos herramientas principales:

1.  **Organizador Multimedia:** Mueve fotos/videos a carpetas por Fecha (Año/Mes).
2.  **Buscador de Duplicados (Nuevo en v2.0):** Escanea una carpeta, detecta archivos idénticos y los aísla para limpieza.

**Ejemplo de Organización:**

- **Ruta de Entrada:** `H:\DCIM\12312\`
- **Ruta de Salida:** `C:\fotos\`
- **Estructura Final:**
  ```
  C:\fotos\
  ├── 2019\
  │   ├── enero\
  │   └── febrero\
  └── 2020\
      └── marzo\
  ```

---

## 🚀 Inicio Rápido

### Para Usuarios (Ejecutable Precompilado)

1. Descarga el último `.exe` desde [Releases](https://github.com/slider66/OrdenaFotos/releases)
2. Ejecuta `OrdenaFotos_Pro.exe`
3. Selecciona carpetas de origen y destino
4. Click en "INICIAR ORGANIZACIÓN"

> [!NOTE]
> Windows puede mostrar una advertencia de seguridad ya que la app no está firmada digitalmente. Haz clic en **"Más información"** → **"Ejecutar de todas formas"** para continuar.

### Para Desarrolladores (Compilar desde Código)

**Requisitos Previos:**

- **Python 3.10+** instalado y añadido al PATH
- **Git** (para clonar el repositorio)

**Pasos:**

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/slider66/OrdenaFotos.git
   cd OrdenaFotos
   ```

2. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

   Dependencias instaladas:

   - `Pillow` - Procesamiento de imágenes y lectura EXIF
   - `ExifRead` - Extracción adicional de metadatos EXIF
   - `ttkbootstrap` - Tema moderno para UI
   - `pyinstaller` - Compilación del ejecutable

3. **Ejecutar la aplicación:**

   ```bash
   python main_gui.py
   ```

4. **Compilar ejecutable (Opcional):**

   ```bash
   build_executable.bat
   ```

   El `.exe` compilado estará en `dist/OrdenaFotos_Pro.exe`

---

## 🛠️ Stack Tecnológico Recomendado

El proyecto se desarrollará utilizando **Python 3.x** debido a su simplicidad, madurez en el manejo del sistema de archivos y las potentes librerías disponibles para la extracción de metadatos.

| Componente                  | Módulo/Librería         | Finalidad Específica                                                  |
| :-------------------------- | :---------------------- | :-------------------------------------------------------------------- |
| **Lenguaje Base**           | Python 3.x              | Implementación de toda la lógica.                                     |
| **Manejo de Archivos**      | `pathlib`, `shutil`     | Búsqueda recursiva, creación de directorios y movimiento de archivos. |
| **Extracción de Metadatos** | `Pillow` (o `ExifRead`) | Lectura de datos EXIF para determinar la fecha de captura de fotos.   |
| **Interfaz (Opcional)**     | Tkinter / Flet          | Interfaz de usuario para la selección de rutas.                       |

---

## 🔑 Lógica Funcional Clave

### 1. Extracción y Priorización de Fechas (EXIF)

Para asegurar la **fecha más coherente** y ordenar correctamente los archivos, se aplicará la siguiente lógica de priorización:

1.  **Prioridad 1 (Metadata):** Intentar extraer la fecha de captura/creación del archivo a partir de los metadatos **EXIF** (para fotos) o tags de video.
2.  **Prioridad 2 (Sistema de Archivos - Creación):** Si no hay metadatos internos válidos, utilizar la **fecha de creación** del archivo registrada por el sistema operativo.
3.  **Prioridad 3 (Sistema de Archivos - Modificación):** Si las fechas anteriores no son accesibles o coherentes (por ejemplo, en sistemas donde la fecha de creación se pierde), se utilizará la **fecha de última modificación**.

La fecha resultante se utilizará para construir la estructura de carpetas `Año/Nombre del Mes`.

### 2. Movimiento Seguro y Validación de Archivos

Para evitar la pérdida de datos, el proceso de transferencia debe ser **atómico** (o simularlo con validación estricta).

- **Paso 1: Movimiento:** Utilizar `shutil.move()` para transferir el archivo de la ruta de origen a la ruta de destino (`RutaSalida\Año\Mes\Archivo.ext`).
- **Paso 2: Validación de Existencia:** Comprobar inmediatamente que el archivo se encuentra en la **ruta de destino**.
- **Paso 3: Validación de Integridad:** Verificar que el **tamaño del archivo** en la ruta de destino **coincide exactamente** con el tamaño del archivo original.
- **Paso 4: Confirmación:** **Solo si la existencia y la integridad (tamaño) están validadas**, se considera que el proceso ha finalizado correctamente. Si la validación falla, se debe registrar un error y mantener el archivo en la ruta de origen.

### 3. Lógica de Limpieza de Carpetas Vacías

Una vez que todos los archivos han sido procesados y movidos, se ejecutará un proceso de limpieza en la ruta de entrada para eliminar cualquier rastro innecesario.

- **Barrido Recursivo Inverso:** Recorrer recursivamente todas las carpetas y subcarpetas de la **ruta de entrada**, comenzando por los directorios más profundos.
- **Comprobación de Vacío:** Utilizar `os.listdir()` para verificar si la carpeta está completamente vacía (sin archivos ni subcarpetas).
- **Eliminación:** Si la carpeta está vacía, se elimina (`os.rmdir()`). Este proceso garantiza que solo las estructuras de carpetas vacías sean removidas, dejando la ruta de origen organizada y limpia.

---

## 💾 Soporte de Archivos Multimedia (Imágenes y Video)

La aplicación debe ser capaz de identificar y procesar una lista exhaustiva de formatos de archivo comunes, RAW y auxiliares (Sidecar) utilizados por fabricantes clave como Apple (iPhone) y Sony.

### A. Extensiones de Imagen Comunes

| Tipo                                | Extensiones                                                                                                          |
| :---------------------------------- | :------------------------------------------------------------------------------------------------------------------- |
| **Estándar**                        | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`                                                    |
| **Alta Eficiencia (Apple/General)** | `.heic`, `.heif` (Formatos modernos de alta compresión).                                                             |
| **Profesional / RAW**               | `.dng`, `.cr2`, `.cr3` (Canon), `.nef` (Nikon), **`.arw` (Sony)**, `.raf` (Fuji), `.orf` (Olympus), `.pef` (Pentax). |

### B. Extensiones de Video Comunes

| Tipo                       | Extensiones                                                                                                            |
| :------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| **Estándar**               | `.mp4`, `.mov` (Nativo de Apple), `.avi`, `.mkv`, `.wmv` (Windows).                                                    |
| **Alta Eficiencia (HEVC)** | Los archivos de video de alta eficiencia suelen utilizar el contenedor **`.mp4`** o **`.mov`** con códec H.265 (HEVC). |

### C. Archivos Auxiliares (Sidecar)

Estos archivos contienen metadatos de edición o información de soporte y deben **moverse junto con su archivo principal** (ej: mover `foto.heic` y `foto.aae` a la misma carpeta de destino).

- **`.aae`**: Archivos de edición de fotos de Apple (iPhone/iPad).
- **`.xmp`**: Metadatos de edición general (Adobe, usados en RAW).
- **`.thm`**: Archivos de miniaturas asociados a videos de cámaras.

---

## 💎 Manejo de Duplicados (Validación por HASH)

Para garantizar que solo se gestionan duplicados verdaderos (mismo contenido, independientemente del nombre del archivo o la fecha de modificación), se aplicará la comprobación de integridad mediante **algoritmos de _hashing_**.

### Flujo de Comprobación

1.  **Cálculo de HASH:** Al encontrar un archivo en la **Ruta de Entrada** (`Origen`) que tiene el **mismo nombre** que un archivo ya existente en la **Ruta de Salida** (`Destino`), la aplicación debe calcular el **HASH criptográfico** (ej. SHA-256) de ambos archivos.
2.  **Verificación:**
    - Si **HASH(Origen) == HASH(Destino)**: El archivo es un duplicado exacto.
    - Si **HASH(Origen) != HASH(Destino)**: Los archivos son diferentes (aunque tengan el mismo nombre) y se debe renombrar el archivo de origen (ej. añadir un sufijo `_dup_1`).
3.  **Acciones para Duplicados Exactos (HASH Coincidente):**

En la versión actual (`v1.0`), la aplicación prioriza la **automatización desatendida** para no interrumpir procesos largos:

- **Duplicados Exactos (Hash Idéntico):** Se aplica la acción **OMITIR**. El archivo de origen se preserva y no se mueve.
- **Colisión de Nombre (Hash Diferente):** Se aplica **RENOMBRADO AUTOMÁTICO** (`archivo_dup_N.ext`).
- **Eliminar Original:** Por seguridad, nunca se borran originales automáticamente en esta versión.

## 🌟 Nuevas Características

### 📁 Exclusión de Carpetas (v2.1)

Excluye carpetas específicas del escaneo para evitar procesar archivos no deseados.

**Características:**

- **Interfaz Visual:** Sección dedicada con listbox mostrando carpetas excluidas
- **Gestión Fácil:** Botones Añadir/Eliminar con soporte multi-selección (Ctrl+Click, Shift+Click)
- **Persistencia Opcional:** Checkbox para guardar exclusiones entre sesiones
- **Rendimiento:** Las carpetas se filtran durante el escaneo (no se accede a ellas)
- **Prevención de Archivos Fantasma:** Salta automáticamente enlaces simbólicos rotos y archivos inexistentes

**Casos de Uso:**

- Excluir carpetas de backup
- Omitir directorios de sincronización en la nube (Dropbox, OneDrive)
- Ignorar carpetas del sistema
- Excluir carpetas temporales o de fotos procesadas
- Omitir descargas de redes sociales (WhatsApp, Instagram)

**Cómo Usar:**

1. Click en botón "➕ Añadir" en sección "Carpetas Excluidas del Escaneo"
2. Seleccionar carpeta a excluir
3. (Opcional) Activar "Guardar exclusiones entre sesiones" para persistir
4. Las carpetas seleccionadas y todas sus subcarpetas serán omitidas durante la organización

### 🧪 Modo Simulación (Dry Run)

Activa la casilla **"Modo Simulación"** para ejecutar todo el análisis sin mover un solo archivo.

- Verifica qué pasaría.
- Genera logs completos.
- Perfecto para ganar confianza antes de ordenar.

### 📝 Logs Persistentes y Visor

- **Historial:** Cada ejecución genera un archivo `operaciones_FECHA.log` en la carpeta destino.
- **Botón "Abrir Log":** Al finalizar, pulsa este botón para ver el reporte inmediato sin buscar el archivo manualmente.

## 🕵️ Buscador de Duplicados (v2.0)

Nueva pestaña dedicada exclusivamente a la limpieza profunda.

1.  **Selecciona una carpeta** (ej: un disco duro externo).
2.  **El programa escanea** todo el contenido buscando archivos idénticos byte a byte (SHA-256).
3.  **Acción Automática:**
    - Mantiene **un** original (la ruta más corta).
    - Mueve **todas** las copias sobrantes a una carpeta `_DUPLICADOS` en la raíz de análisis.
4.  **Resultado:** Puedes entrar a `_DUPLICADOS` y borrar todo con confianza, sabiendo que tienes una copia segura en su lugar original.

---

Este esquema de manejo de duplicados por HASH es muy robusto.

Como esta aplicación involucra mover y manipular archivos de iPhone, puede ser útil ver cómo otros usuarios gestionan la transferencia de estos archivos. Aquí tienes un video que explica cómo trabajar con archivos HEIC en Windows.

[Convertir HEIC a JPG en Windows | Archivos AAE | Configurar celular (BONUS)](https://www.youtube.com/watch?v=pdDEHuntbeA)

Este video es relevante porque aborda directamente el manejo de formatos específicos de iPhone (HEIC y AAE), los cuales se incluyen en tu lista de extensiones.

---

## 🚀 Compilación y Ejecución

Si deseas generar tu propio ejecutable `.exe` a partir del código fuente (por ejemplo, tras modificar algo), se incluye un script automatizado para Windows.

### Requisitos Previos

- Tener **Python 3.x** instalado y agregado al PATH.
- (Opcional) Un entorno virtual activo, aunque el script gestionará dependencias.

### Pasos para Compilar

1.  Abre la carpeta del proyecto.
2.  Haz doble clic en el archivo **`build_executable.bat`**.
3.  El script instalará automáticamente las dependencias necesarias (`Pillow`, `ttkbootstrap`, `pyinstaller`, etc.).
4.  Al finalizar, encontrarás el nuevo ejecutable en la carpeta **`dist/OrdenaFotos_Pro.exe`**.

### Ejecución

Simplemente abre el archivo `.exe` generado.

> [!WARNING] > **¿Windows bloquea la ejecución?**
> Al no estar firmado digitalmente (costoso), Windows Defender puede mostrar "Windows protegió su PC".
>
> 1. Haz clic en **"Más información"**.
> 2. Pulsa el botón **"Ejecutar de todas formas"**.
>
> **Alternativa (Desbloqueo Permanente):**
>
> 1. Clic derecho en el `.exe` > Propiedades.
> 2. Marca la casilla **"Desbloquear"** (Unblock) abajo a la derecha.
> 3. Aplicar y Aceptar.

---

## 🛡️ Fiabilidad y Pruebas Realizadas

Esta aplicación ha sido sometida a una batería de tests automatizados para garantizar la seguridad de tus archivos.

### ✅ Cobertura de Pruebas

1. **Integridad de Datos:** Verificado que el cálculo de `SHA-256` detecta diferencias de 1 byte y coincidencias exactas.
2. **Prioridad de Fechas:** Verificado el fallback correcto: _EXIF > Creación > Modificación_.

### 3. Gestión de Duplicados 👯

- **Colisión de Nombre (Contenido diferente):** Si el archivo existe pero es distinto, se renombra automáticamente (ej: `foto_dup_1.jpg`) y se guarda junto al original.
- **Duplicado Exacto (Mismo contenido):** Si el archivo ya existe y es idéntico (verificado por Hash SHA-256), el nuevo archivo **SE MUEVE** a una carpeta especial llamada `_DUPLICADOS_REVISAR` dentro del destino.
  - Esto te permite revisar y borrar manualmente los duplicados sin miedo a perder nada.
  - Nunca se sobrescribe nada automáticamente.

4. **Resiliencia a Bucles:**
   - Detecta si el archivo origen y destino son la misma ruta física (Idempotencia) y lo omite.
   - Detiene bucles infinitos si la carpeta destino está dentro del origen.
5. **No Destructivo:** Confirmado que NUNCA se borra el origen sin antes validar la existencia y tamaño byte-a-byte en el destino.

# OrdenaFotos
