import unittest
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import hashlib
from src.integrity import calculate_hash, check_duplicate
from src.scanner import scan_directory, MediaGroup
from src.date_extractor import get_date_taken

class TestCoreFunctions(unittest.TestCase):
    def setUp(self):
        # Crear directorio temporal para pruebas
        self.test_dir = Path(tempfile.mkdtemp())
        self.file_a = self.test_dir / "fileA.jpg"
        self.file_b = self.test_dir / "fileB.jpg"
        
        # Crear archivos dummy
        with open(self.file_a, "wb") as f:
            f.write(b"content_123")
        
        with open(self.file_b, "wb") as f:
            f.write(b"content_123") # Mismo contenido

        self.file_c = self.test_dir / "fileC.jpg"
        with open(self.file_c, "wb") as f:
            f.write(b"content_DIFFERENT")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_calculate_hash(self):
        # SHA256 de "content_123"
        expected_hash = hashlib.sha256(b"content_123").hexdigest()
        self.assertEqual(calculate_hash(self.file_a), expected_hash)

    def test_check_duplicate_true(self):
        self.assertTrue(check_duplicate(self.file_a, self.file_b))

    def test_check_duplicate_false(self):
        self.assertFalse(check_duplicate(self.file_a, self.file_c))

    def test_date_fallback(self):
        # Como son archivos creados ahora, get_date_taken debería devolver algo muy reciente (hoy)
        # Probamos el fallback a sistema de archivos ya que no tienen EXIF
        date = get_date_taken(self.file_a)
        now = datetime.now()
        # Verificar que es del mismo año y mes (margen error minimo)
        self.assertEqual(date.year, now.year)
        self.assertEqual(date.month, now.month)

class TestScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Crear estructura:
        # /foto1.jpg
        # /foto1.aae (sidecar)
        # /sub/video1.mp4
        # /texto.txt (ignorar)
        
        (self.test_dir / "sub").mkdir()
        
        Path(self.test_dir / "foto1.jpg").touch()
        Path(self.test_dir / "foto1.aae").touch()
        Path(self.test_dir / "sub/video1.mp4").touch()
        Path(self.test_dir / "texto.txt").touch()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_directory(self):
        results = list(scan_directory(self.test_dir))
        
        # Debemos encontrar 2 grupos (foto1 y video1)
        self.assertEqual(len(results), 2)
        
        # Verificar contenido
        files_found = {g.main_file.name: g for g in results}
        
        self.assertIn("foto1.jpg", files_found)
        self.assertIn("video1.mp4", files_found)
        
        # Verificar sidecar
        foto_group = files_found["foto1.jpg"]
        self.assertEqual(len(foto_group.sidecars), 1)
        self.assertEqual(foto_group.sidecars[0].name, "foto1.aae")

if __name__ == '__main__':
    unittest.main()
