import os
import shutil
from pathlib import Path
from typing import Tuple, Optional

from .date_extractor import get_date_taken
from .integrity import check_duplicate
from .scanner import MediaGroup

# Constantes de Resultados
STATUS_SUCCESS = "SUCCESS"
STATUS_SKIPPED = "SKIPPED"
STATUS_ERROR = "ERROR"
STATUS_DUPLICATE = "DUPLICATE_FOUND"

class OperationResult:
    def __init__(self, status: str, message: str, destination: Optional[Path] = None):
        self.status = status
        self.message = message
        self.destination = destination

def move_media_safe(media_group: MediaGroup, base_dest_path: Path, duplicate_action: str = 'ask', dry_run: bool = False) -> OperationResult:
    """
    Mueve un grupo multimedia de forma segura a la estructura organizada por fecha.
    
    Args:
        media_group: Objeto con archivo main y sidecars.
        base_dest_path: Ruta base de destino
        duplicate_action: 'ask', 'overwrite', 'skip', 'delete_original'
        dry_run: Si es True, no mueve ni borra nada, solo simula.
    """
    try:
        # 1. Determinar Fecha y Ruta Destino
        date = get_date_taken(media_group.main_file)
        
        # Nombres de carpeta en español
        month_names = ["00", "01-enero", "02-febrero", "03-marzo", "04-abril", "05-mayo", "06-junio", 
                       "07-julio", "08-agosto", "09-septiembre", "10-octubre", "11-noviembre", "12-diciembre"]
        
        folder_year = str(date.year)
        folder_month = month_names[date.month] if 1 <= date.month <= 12 else "unknown"
        
        target_dir = base_dest_path / folder_year / folder_month
        
        # 1.5. Verificar IDEMPOTENCIA
        target_main_path = target_dir / media_group.main_file.name
        
        try:
            if media_group.main_file.resolve() == target_main_path.resolve():
                return OperationResult(STATUS_SKIPPED, "Archivo ya organizado (Misma ruta)")
        except OSError:
            if str(media_group.main_file.absolute()) == str(target_main_path.absolute()):
                 return OperationResult(STATUS_SKIPPED, "Archivo ya organizado (Misma ruta)")

        # 2. Verificar Colisiones
        created_by_dry_run = False # Flag para saber si simulamos que existe

        if target_main_path.exists():
            is_exact_dup = check_duplicate(media_group.main_file, target_main_path)
            
            if is_exact_dup:
                if duplicate_action == 'ask':
                    return OperationResult(STATUS_DUPLICATE, "Duplicado exacto detectado", destination=target_main_path)
                elif duplicate_action == 'skip':
                    return OperationResult(STATUS_SKIPPED, "Omitido por duplicado exacto")
                elif duplicate_action == 'delete_original':
                    if not dry_run: _safe_delete_group(media_group)
                    return OperationResult(STATUS_SUCCESS, "Original eliminado (duplicado) [DRY RUN]" if dry_run else "Original eliminado (duplicado)")
                elif duplicate_action == 'overwrite':
                    if not dry_run:
                        os.remove(target_main_path)
                        for s in media_group.sidecars:
                             s_t = target_dir / s.name
                             if s_t.exists(): os.remove(s_t)
            else:
                # Falso duplicado -> Renombrar
                stem = media_group.main_file.stem
                suffix = media_group.main_file.suffix
                counter = 1
                while True:
                    new_name = f"{stem}_dup_{counter}{suffix}"
                    target_main_path = target_dir / new_name
                    if not target_main_path.exists():
                        break
                    if check_duplicate(media_group.main_file, target_main_path):
                         # Ya existe la copia renombrada igual
                         if duplicate_action == 'skip':
                             return OperationResult(STATUS_SKIPPED, f"Omitido, ya existe como {new_name}")
                    counter += 1

        # 3. Ejecución del Movimiento
        if dry_run:
            return OperationResult(STATUS_SUCCESS, f"Se movería a: {target_main_path} [SIMULACION]", destination=target_main_path)

        # Crear directorio
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Mover Main
        _copy_validate_delete(media_group.main_file, target_main_path)
        
        # Mover Sidecars
        new_stem = target_main_path.stem 
        for sidecar in media_group.sidecars:
            dest_sidecar_name = f"{new_stem}{sidecar.suffix}"
            dest_sidecar_path = target_dir / dest_sidecar_name
            if dest_sidecar_path.exists():
                os.remove(dest_sidecar_path)
            _copy_validate_delete(sidecar, dest_sidecar_path)

        return OperationResult(STATUS_SUCCESS, "Movido correctamente", destination=target_main_path)

    except Exception as e:
        return OperationResult(STATUS_ERROR, f"Error critico: {str(e)}")

def _copy_validate_delete(source: Path, destination: Path):
    """
    Realiza la operación atómica simulada: Copiar -> Verificar Tamaño -> Borrar Origen.
    Garantiza que no se pierdan datos.
    """
    # 1. Copiar preservando metadatos (shutil.copy2)
    shutil.copy2(source, destination)
    
    # 2. Validar Existencia y Tamaño
    if not destination.exists():
        raise IOError(f"El archivo destino no se creó: {destination}")
    
    src_size = source.stat().st_size
    dst_size = destination.stat().st_size
    
    if src_size != dst_size:
        # Fallo de integridad. Intentar limpiar destino sucio y abortar.
        os.remove(destination)
        raise IOError(f"Error de integridad. Tamaños difieren ({src_size} vs {dst_size})")
    
    # 3. Borrar Origen (Solo si validación pasó)
    os.remove(source)

def _safe_delete_group(media_group: MediaGroup):
    """Borra el grupo de archivos de origen (usado cuando se decide borrar duplicado)."""
    if media_group.main_file.exists():
        os.remove(media_group.main_file)
    for s in media_group.sidecars:
        if s.exists():
            os.remove(s)
