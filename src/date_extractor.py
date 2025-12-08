import os
import struct
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import exifread

# Definición de Extensiones Soportadas según README
IMG_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',  # Estándar
    '.heic', '.heif',  # Alta Eficiencia
    '.dng', '.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.pef'  # RAW
}

VIDEO_EXTENSIONS = {
    '.mp4', '.mov',  # Estándar / Alta Eficiencia (Contenedores comunes)
    '.avi', '.mkv', '.wmv'  # Otros
}

def get_date_taken(file_path: Path) -> datetime:
    """
    Intenta extraer la fecha de captura/creación del archivo con la siguiente prioridad:
    1. EXIF (para imágenes) o Tags MP4/MOV (para videos)
    2. Sistema de archivos - Fecha de Creación (ctime)
    3. Sistema de archivos - Fecha de Modificación (mtime)
    """
    ext = file_path.suffix.lower()
    
    # 1. Prioridad 1: Metadata Interna
    date_metadata = None
    
    if ext in IMG_EXTENSIONS:
        date_metadata = _get_exif_date(file_path)
    elif ext in VIDEO_EXTENSIONS:
        date_metadata = _get_video_date(file_path)

    if date_metadata:
        return date_metadata

    # 2. Prioridad 2: Sistema de Archivos - Creación
    try:
        # En Windows, st_ctime es la fecha de creación.
        timestamp = os.path.getctime(file_path)
        return datetime.fromtimestamp(timestamp)
    except OSError:
        pass

    # 3. Prioridad 3: Sistema de Archivos - Modificación
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except OSError:
        # Fallback final
        return datetime.now()

def _get_exif_date(file_path: Path) -> datetime:
    """Extracción auxiliar de metadatos EXIF para imágenes."""
    # Intento 1: Usando Pillow
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if exif_data:
                # Buscamos DateTimeOriginal (36867) o DateTimeDigitized (36868) o DateTime (306)
                for tag_id in [36867, 36868, 306]:
                    if tag_id in exif_data:
                        date_str = exif_data[tag_id]
                        try:
                            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            continue
    except Exception:
        pass

    # Intento 2: Usando ExifRead (Para RAWs y fallbacks)
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal', details=False)
            keys = ['EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Image DateTime']
            for key in keys:
                if key in tags:
                    date_str = str(tags[key])
                    try:
                        return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        continue
    except Exception:
        pass

    return None

def _get_video_date(file_path: Path) -> datetime:
    """
    Intento básico de extraer fecha de creación de contenedores MP4/MOV.
    Busca el átomo 'mvhd' dentro de 'moov'.
    La fecha en MP4 son segundos desde el 1 de Enero de 1904 (UTC).
    """
    try:
        # Solo intentamos parsear MP4/MOV nativos
        if file_path.suffix.lower() not in ['.mp4', '.mov']:
            return None

        with open(file_path, 'rb') as f:
            while True:
                # Leer tamaño y tipo de átomo (Header de 8 bytes)
                atom_header = f.read(8)
                if len(atom_header) < 8:
                    break
                
                atom_size, atom_type = struct.unpack('>I4s', atom_header)
                atom_type = atom_type.decode('ascii')

                if atom_type == 'moov':
                    # Entramos al contenedor moov (sin avanzar, ya estamos dentro lógicamente tras el header)
                    # Pero 'moov' es un contenedor, así que sus datos son sub-átomos. 
                    # No saltamos, procesamos el contenido del moov buscando mvhd.
                    # El contenido del moov es: sub-atoms.
                    # Leemos sub-atoms hasta encontrar mvhd
                    end_of_moov = f.tell() + atom_size - 8
                    
                    while f.tell() < end_of_moov:
                        sub_header = f.read(8)
                        if len(sub_header) < 8:
                            break
                        sub_size, sub_type = struct.unpack('>I4s', sub_header)
                        sub_type = sub_type.decode('ascii')
                        
                        if sub_type == 'mvhd':
                            # Movie Header Atom encontrado
                            # Estructura v0: 1 byte version, 3 bytes flags, 4 bytes creation_time ...
                            data = f.read(sub_size - 8)
                            version = data[0]
                            
                            # Creation time está en offsets diferentes según versión
                            if version == 0:
                                # Version 0: creation_time está en byte 4 (4 bytes)
                                # data[0]: version, data[1-3]: flags
                                # data[4-7]: creation_time
                                creation_time = struct.unpack('>I', data[4:8])[0]
                            elif version == 1:
                                # Version 1 (64-bit): creation_time está en byte 4 (8 bytes)
                                creation_time = struct.unpack('>Q', data[4:12])[0]
                            else:
                                return None

                            # MP4 epoch: 1904-01-01
                            mp4_epoch = datetime(1904, 1, 1)
                            return mp4_epoch + timedelta(seconds=creation_time)
                        else:
                            # Saltar sub-átomo si no es mvhd
                            f.seek(sub_size - 8, 1)
                    break
                else:
                    # Saltar átomo si no es moov (mvhd suele estar dentro de moov)
                    # Si atom_size es 1, es tamaño extendido (no soportado en este script simple por ahora)
                    if atom_size == 1: 
                        break 
                    f.seek(atom_size - 8, 1)
    except Exception:
        pass
    
    return None
