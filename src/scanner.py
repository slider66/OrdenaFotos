import os
from pathlib import Path
from typing import Generator, List, Set

# Definición de extensiones que consideramos "Multimedia"
# (Sincronizado con date_extractor y README)
IMG_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
    '.heic', '.heif',
    '.dng', '.cr2', '.cr3', '.nef', '.arw', '.raf', '.orf', '.pef'
}

VIDEO_EXTENSIONS = {
    '.mp4', '.mov', '.avi', '.mkv', '.wmv'
}

# Archivos sidecar que deben moverse junto al principal
SIDECAR_EXTENSIONS = {'.aae', '.xmp', '.thm'}

ALL_MEDIA_EXTENSIONS = IMG_EXTENSIONS.union(VIDEO_EXTENSIONS)

class MediaGroup:
    """
    Representa un archivo multimedia principal y sus archivos auxiliares (sidecars).
    Ejemplo: 'foto.heic' (main) + 'foto.aae' (sidecar)
    """
    def __init__(self, main_file: Path):
        self.main_file = main_file
        self.sidecars: List[Path] = []

    def add_sidecar(self, sidecar: Path):
        self.sidecars.append(sidecar)
    
    def __repr__(self):
        return f"<MediaGroup main={self.main_file.name} sidecars={len(self.sidecars)}>"

def scan_directory(source_dir: Path) -> Generator[MediaGroup, None, None]:
    """
    Recorre recursivamente el directorio buscando archivos multimedia validos.
    Agrupa automáticamente los archivos sidecar (.xmp, .aae) con su archivo principal
    si comparten el mismo nombre base.
    """
    source_path = Path(source_dir)
    
    for root, _, files in os.walk(source_path):
        root_path = Path(root)
        
        # Set de nombres de archivo (minusculas) en el directorio actual para búsqueda rápida
        # Guardamos el nombre real para poder reconstruir el path con el casing correcto
        file_map = {f.lower(): f for f in files}
        
        for filename in files:
            file_path = root_path / filename
            suffix = file_path.suffix.lower()
            
            # Solo procesamos si es una extensión multimedia válida (Main File)
            if suffix in ALL_MEDIA_EXTENSIONS:
                media_group = MediaGroup(file_path)
                
                # Buscar posibles sidecars asociados a este archivo
                stem = file_path.stem
                
                for sidecar_ext in SIDECAR_EXTENSIONS:
                    # Construir nombre candidato: nombrefichero.xmp
                    # Nota: A veces el sidecar es nombre.ext.xmp (foto.jpg.xmp) o nombre.xmp (foto.xmp)
                    # El README da ejemplo: foto.heic y foto.aae -> mismo stem.
                    # Asumimos coincidencia de stem.
                    
                    candidate_name_lower = f"{stem}{sidecar_ext}".lower()
                    
                    if candidate_name_lower in file_map:
                        real_sidecar_name = file_map[candidate_name_lower]
                        sidecar_path = root_path / real_sidecar_name
                        media_group.add_sidecar(sidecar_path)
                
                yield media_group
