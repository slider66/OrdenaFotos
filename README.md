# 📂 Utilidad de Organización Multimedia Local

## 🎯 Objetivo del Proyecto

Crear una aplicación de escritorio local, sencilla y robusta, diseñada para automatizar la organización de archivos multimedia (fotos y videos) desde una ruta de origen a una ruta de destino. El criterio de ordenamiento es la **fecha de creación/captura** de los archivos, garantizando la **integridad de los datos** durante el proceso de movimiento y manteniendo limpia la ruta de origen.

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

## 🌟 Nuevas Características (v1.1)

### 🧪 Modo Simulación (Dry Run)

Activa la casilla **"Modo Simulación"** para ejecutar todo el análisis sin mover un solo archivo.

- Verifica qué pasaría.
- Genera logs completos.
- Perfecto para ganar confianza antes de ordenar.

### 📝 Logs Persistentes y Visor

- **Historial:** Cada ejecución genera un archivo `operaciones_FECHA.log` en la carpeta destino.
- **Botón "Abrir Log":** Al finalizar, pulsa este botón para ver el reporte inmediato sin buscar el archivo manualmente.

---

Este esquema de manejo de duplicados por HASH es muy robusto.

Como esta aplicación involucra mover y manipular archivos de iPhone, puede ser útil ver cómo otros usuarios gestionan la transferencia de estos archivos. Aquí tienes un video que explica cómo trabajar con archivos HEIC en Windows.

[Convertir HEIC a JPG en Windows | Archivos AAE | Configurar celular (BONUS)](https://www.youtube.com/watch?v=pdDEHuntbeA)

Este video es relevante porque aborda directamente el manejo de formatos específicos de iPhone (HEIC y AAE), los cuales se incluyen en tu lista de extensiones.

http://googleusercontent.com/youtube_content/2

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

Simplemente abre el archivo `.exe` generado. No requiere instalación ni tener Python en la máquina donde se vaya a usar.

---

## 🛡️ Fiabilidad y Pruebas Realizadas

Esta aplicación ha sido sometida a una batería de tests automatizados para garantizar la seguridad de tus archivos.

### ✅ Cobertura de Pruebas

1. **Integridad de Datos:** Verificado que el cálculo de `SHA-256` detecta diferencias de 1 byte y coincidencias exactas.
2. **Prioridad de Fechas:** Verificado el fallback correcto: _EXIF > Creación > Modificación_.
3. **Manejo de Duplicados:**
   - **Exactos:** Test pasado confirmando que OMITIR no borra el original.
   - **Colisión de Nombre:** Test pasado confirmando RENOMBRADO automático (`_dup_N`) si el contenido difiere.
4. **Resiliencia a Bucles:**
   - Detecta si el archivo origen y destino son la misma ruta física (Idempotencia) y lo omite.
   - Detiene bucles infinitos si la carpeta destino está dentro del origen.
5. **No Destructivo:** Confirmado que NUNCA se borra el origen sin antes validar la existencia y tamaño byte-a-byte en el destino.

# OrdenaFotos
