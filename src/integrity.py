import hashlib
from pathlib import Path

def calculate_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Calcula el hash SHA-256 de un archivo de manera eficiente (por chunks)."""
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Leer el archivo por bloques para no saturar la memoria con archivos grandes (videos)
        for byte_block in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(byte_block)
            
    return sha256_hash.hexdigest()

def check_duplicate(file_a: Path, file_b: Path) -> bool:
    """
    Compara dos archivos calculando sus hashes.
    Retorna True si son idénticos (duplicados exactos), False si no.
    """
    if not file_a.exists() or not file_b.exists():
        raise FileNotFoundError("Uno o ambos archivos no existen.")
    
    # Optimización rápida: Si los tamaños son diferentes, no son el mismo archivo.
    if file_a.stat().st_size != file_b.stat().st_size:
        return False

    hash_a = calculate_hash(file_a)
    hash_b = calculate_hash(file_b)
    
    return hash_a == hash_b
