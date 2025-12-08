import os
import shutil
from pathlib import Path
from typing import Generator, List, Dict, Tuple
from .integrity import calculate_hash
from .scanner import ALL_MEDIA_EXTENSIONS

class DuplicateResult:
    def __init__(self, original: Path, duplicates: List[Path]):
        self.original = original
        self.duplicates = duplicates

def scan_and_move_duplicates(root_path: Path) -> Generator[str, None, None]:
    """
    Escanea recursivamente busacndo duplicados exactos (mismo contenido SHA-256).
    Mueve los duplicados a una carpeta _DUPLICADOS en la raíz.
    Yields status messages.
    """
    root = Path(root_path)
    dup_dest_dir = root / "_DUPLICADOS"
    
    yield f"Analizando estructura de archivos en: {root}"
    
    # 1. Agrupar por tamaño (Optimización inicial)
    size_map: Dict[int, List[Path]] = {}
    total_files = 0
    
    for dirpath, _, filenames in os.walk(root):
        # Evitar escanear la propia carpeta de duplicados si ya existe
        if "_DUPLICADOS" in Path(dirpath).parts:
            continue
            
        for f in filenames:
            file_path = Path(dirpath) / f
            # Opcional: Filtrar solo multimedia? 
            # El usuario dijo "busca duplicados", idealmente de todo, pero para seguridad
            # nos centramos en lo que solemos manejar o todo? 
            # La solicitud dice "busca duplicados... y todos los que encuentre". 
            # Haremos scan general para ser útiles, o restringido?
            # Mejor general, pero ignorando archivos de sistema/ocultos si los hubiera.
            
            try:
                size = file_path.stat().st_size
                if size > 0: # Ignorar archivos vacíos
                    if size not in size_map:
                        size_map[size] = []
                    size_map[size].append(file_path)
                    total_files += 1
            except OSError:
                pass

    yield f"Total archivos encontrados: {total_files}. Analizando candidatos..."

    # 2. Calcular Hash solo para colisiones de tamaño
    duplicates_found = 0
    moved_count = 0
    
    for size, files in size_map.items():
        if len(files) < 2:
            continue
            
        # Agrupar por Hash
        hash_map: Dict[str, List[Path]] = {}
        
        for file_path in files:
            try:
                # Yield para UI responsiveness en archivos grandes
                if size > 10 * 1024 * 1024: 
                    yield f"Hash calculando: {file_path.name}..."
                
                file_hash = calculate_hash(file_path)
                if file_hash not in hash_map:
                    hash_map[file_hash] = []
                hash_map[file_hash].append(file_path)
            except OSError:
                continue

        # 3. Procesar Duplicados
        for file_hash, same_content_files in hash_map.items():
            if len(same_content_files) > 1:
                # Tenemos duplicados
                duplicates_found += len(same_content_files) - 1
                
                # Criterio Original: Ruta más corta (menor profundidad)
                # Si empate, ordenar alfabéticamente
                same_content_files.sort(key=lambda p: (len(p.parts), p.name))
                
                original = same_content_files[0]
                dupes = same_content_files[1:]
                
                # Mover duplicados
                if not dup_dest_dir.exists():
                    dup_dest_dir.mkdir()
                    
                for dup in dupes:
                    yield f"Duplicado detectado: {dup.name} (Original: {original.name})"
                    
                    try:
                        # Calcular destino
                        dest_path = dup_dest_dir / dup.name
                        
                        # Manejar colisión de nombre en carpeta _DUPLICADOS
                        if dest_path.exists():
                            stem = dest_path.stem
                            suffix = dest_path.suffix
                            counter = 1
                            while dest_path.exists():
                                dest_path = dup_dest_dir / f"{stem}_dup_{counter}{suffix}"
                                counter += 1
                        
                        # Mover con shutil.move
                        shutil.move(str(dup), str(dest_path))
                        moved_count += 1
                        
                        # Intentar limpiar carpeta vacía
                        try:
                            if not any(dup.parent.iterdir()):
                                dup.parent.rmdir()
                        except:
                            pass
                            
                    except Exception as e:
                        yield f"ERROR moviendo {dup.name}: {e}"

    yield f"Finalizado. {duplicates_found} duplicados detectados. {moved_count} movidos a '_DUPLICADOS'."
