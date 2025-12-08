import unittest
import shutil
import tempfile
from pathlib import Path
from src.deduplicator import scan_and_move_duplicates

class TestDeduplicator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        self.dup_dir = self.root / "_DUPLICADOS"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, path: Path, content: bytes):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(content)

    def test_deduplication(self):
        # Crear estructura
        # root/original.txt
        # root/sub/copia.txt (Duplicado)
        # root/other/unico.txt
        
        content_a = b"Contenido A"
        content_b = b"Contenido B"
        
        f1 = self.root / "original.txt"
        f2 = self.root / "sub" / "copia.txt"
        f3 = self.root / "other" / "unico.txt"
        
        self.create_file(f1, content_a)
        self.create_file(f2, content_a) # Duplicado de f1
        self.create_file(f3, content_b)
        
        # Ejecutar deduplicador
        # Consumir el generador
        for _ in scan_and_move_duplicates(self.root):
            pass
            
        # Verificaciones
        # 1. f1 debe existir (es el original por tener ruta más corta)
        self.assertTrue(f1.exists(), "Original should remain")
        
        # 2. f2 debe haber desaparecido
        self.assertFalse(f2.exists(), "Duplicate should be moved")
        
        # 3. f2 debe estar en _DUPLICADOS con nombre 'copia.txt'
        moved_dup = self.dup_dir / "copia.txt"
        self.assertTrue(moved_dup.exists(), "Duplicate should be in _DUPLICADOS")
        
        # 4. f3 debe estar intacto
        self.assertTrue(f3.exists(), "Unique file should remain")

    def test_name_collision_in_duplicates(self):
        # Caso: Dos duplicados con el mismo nombre
        content = b"MISMO CONTENIDO"
        
        f1 = self.root / "orig.txt"
        f2 = self.root / "d1" / "dup.txt"
        f3 = self.root / "d2" / "dup.txt"
        
        self.create_file(f1, content)
        self.create_file(f2, content)
        self.create_file(f3, content)
        
        for _ in scan_and_move_duplicates(self.root):
            pass
            
        self.assertTrue(f1.exists())
        self.assertFalse(f2.exists())
        self.assertFalse(f3.exists())
        
        # Deben haber 2 archivos en duplicados
        dups = list(self.dup_dir.glob("*"))
        self.assertEqual(len(dups), 2)
        
        # Uno será dup.txt y el otro dup_dup_1.txt
        names = {f.name for f in dups}
        self.assertIn("dup.txt", names)
        # La lógica de renombrado añade _dup_N
        self.assertTrue(any("dup_dup_" in n for n in names))

if __name__ == "__main__":
    unittest.main()
