import os
from pathlib import Path

def clean_empty_directories(directory: Path):
    """
    Recorre el directorio de abajo hacia arriba (bottom-up) y elimina las carpetas que estén vacías.
    """
    # os.walk con topdown=False permite procesar primero los hijos y luego los padres.
    # Esto es crucial: si eliminas una subcarpeta y la carpeta padre queda vacía, 
    # el loop la verá vacía cuando llegue a ella y también la eliminará.
    
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in dirs:
            dir_path = Path(root) / name
            try:
                # Intentar borrar. rmdir solo borra si está vacío.
                # Hacemos check manual antes para evitar excepciones innecesarias, 
                # aunque rmdir ya es atómico en ese sentido.
                if not any(os.scandir(dir_path)):
                    os.rmdir(dir_path)
                    # print(f"Directorio vacío eliminado: {dir_path}")
            except OSError:
                # Puede fallar si hay archivos ocultos del sistema (ej .DS_Store, Thumbs.db)
                # o permisos. Ignoramos silenciosamente para no detener el proceso.
                pass
