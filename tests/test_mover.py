import unittest
import os
import shutil
import tempfile
from pathlib import Path
from src.mover import move_media_safe, STATUS_SUCCESS, STATUS_DUPLICATE, STATUS_SKIPPED
from src.scanner import MediaGroup
from src.cleaner import clean_empty_directories

class TestMoverAndCleaner(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(tempfile.mkdtemp())
        self.src_dir = self.root_dir / "src"
        self.dst_dir = self.root_dir / "dst"
        
        self.src_dir.mkdir()
        self.dst_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.root_dir)

    def test_move_simple(self):
        # Crear archivo origen
        f = self.src_dir / "test.jpg"
        with open(f, "wb") as file:
            file.write(b"data")
            
        group = MediaGroup(f)
        
        # Ejecutar move
        result = move_media_safe(group, self.dst_dir)
        
        self.assertEqual(result.status, STATUS_SUCCESS)
        self.assertFalse(f.exists()) # Origen borrado
        
        # Verificar destino (debe estar en Año/Mes/)
        # Como no tiene exif, usará fecha hoy.
        # Buscamos recursivamente en dst para encontrarlo
        found = list(self.dst_dir.rglob("test.jpg"))
        self.assertEqual(len(found), 1)

    def test_clean_empty(self):
        # Crear estructura vacía
        d1 = self.src_dir / "empty1"
        d1.mkdir()
        d2 = self.src_dir / "empty1" / "empty2"
        d2.mkdir()
        
        # Ejecutar cleaner
        clean_empty_directories(self.src_dir)
        
        self.assertFalse(d2.exists())
        self.assertFalse(d1.exists())
        self.assertTrue(self.src_dir.exists()) # Raíz no se borra

    def test_duplicate_skip(self):
        # 1. Crear archivo en Origen
        src_file = self.src_dir / "dup.jpg"
        with open(src_file, "wb") as f:
            f.write(b"CONTENIDO_DUPLICADO")
            
        # 2. Simular que YA existe en destino (en la carpeta correcta de Año/Mes)
        # Necesitamos saber dónde lo va a poner. Como no hay EXIF, es fecha hoy.
        from datetime import datetime
        now = datetime.now()
        month_names = ["00", "01-enero", "02-febrero", "03-marzo", "04-abril", "05-mayo", "06-junio", 
                       "07-julio", "08-agosto", "09-septiembre", "10-octubre", "11-noviembre", "12-diciembre"]
        
        target_folder = self.dst_dir / str(now.year) / month_names[now.month]
        target_folder.mkdir(parents=True)
        dst_file = target_folder / "dup.jpg"
        
        with open(dst_file, "wb") as f:
            f.write(b"CONTENIDO_DUPLICADO") # IDÉNTICO
            
        # 3. Mover con acción 'skip'
        group = MediaGroup(src_file)
        result = move_media_safe(group, self.dst_dir, duplicate_action='skip')
        
        # 4. Verificar
        self.assertEqual(result.status, STATUS_SKIPPED)
        self.assertTrue(src_file.exists()) # El original NO se debe borrar si se omite
        self.assertTrue(dst_file.exists())

    def test_rename_on_collision(self):
        # 1. Crear archivo en Origen
        src_file = self.src_dir / "collision.jpg"
        with open(src_file, "wb") as f:
            f.write(b"CONTENIDO_NUEVO")
            
        # 2. Simular archivo en destino con MISMO NOMBRE pero DIFERENTE contenido
        from datetime import datetime
        now = datetime.now()
        month_names = ["00", "01-enero", "02-febrero", "03-marzo", "04-abril", "05-mayo", "06-junio", 
                       "07-julio", "08-agosto", "09-septiembre", "10-octubre", "11-noviembre", "12-diciembre"]
        
        target_folder = self.dst_dir / str(now.year) / month_names[now.month]
        target_folder.mkdir(parents=True, exist_ok=True)
        dst_file = target_folder / "collision.jpg"
        
        with open(dst_file, "wb") as f:
            f.write(b"CONTENIDO_VIEJO_DISTINTO") 
            
        # 3. Mover
        group = MediaGroup(src_file)
        result = move_media_safe(group, self.dst_dir)
        
        # 4. Verificar
        self.assertEqual(result.status, STATUS_SUCCESS)
        self.assertFalse(src_file.exists()) # Se movio
        
        # El archivo destino original debe seguir igual
        with open(dst_file, "rb") as f:
            self.assertEqual(f.read(), b"CONTENIDO_VIEJO_DISTINTO")
            
        # Debe haber aparecido uno nuevo renombrado
        renamed_file = target_folder / "collision_dup_1.jpg"
        self.assertTrue(renamed_file.exists())
        with open(renamed_file, "rb") as f:
            self.assertEqual(f.read(), b"CONTENIDO_NUEVO")

if __name__ == '__main__':
    unittest.main()
