import unittest
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from src.mover import move_media_safe, STATUS_SKIPPED, STATUS_SUCCESS
from src.scanner import MediaGroup

class TestSameDir(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        # En este caso, Source y Destination son EL MISMO
        self.src_dir = self.test_dir
        self.dst_dir = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_already_organized_file(self):
        # 1. Crear un archivo que YA está en la ruta correcta
        # Supongamos fecha hoy
        now = datetime.now()
        month_names = ["00", "01-enero", "02-febrero", "03-marzo", "04-abril", "05-mayo", "06-junio", 
                       "07-julio", "08-agosto", "09-septiembre", "10-octubre", "11-noviembre", "12-diciembre"]
        
        folder_path = self.src_dir / str(now.year) / month_names[now.month]
        folder_path.mkdir(parents=True, exist_ok=True)
        
        file_path = folder_path / "already_here.jpg"
        with open(file_path, "wb") as f:
            f.write(b"content") # Sin metadatos -> usará fecha hoy -> COINCIDE con carpeta actual
            
        # 2. Intentar moverlo
        group = MediaGroup(file_path)
        result = move_media_safe(group, self.dst_dir)
        
        # 3. Verificar
        # Esperamos que detecte que es el mismo sitio y lo omita
        # Ojo: shutil.move lanza error si src==dst. Mover.py debería capturarlo o prevenirlo.
        
        if result.status == STATUS_SUCCESS:
             # Si dice success, verificamos que el archivo siga ahí y no haya pasado nada raro
             self.assertTrue(file_path.exists())
        elif result.status == STATUS_SKIPPED:
             # Idealmente debería ser SKIPPED
             self.assertTrue(file_path.exists())
        else:
             self.fail(f"Status inesperado: {result.status} - {result.message}")

if __name__ == '__main__':
    unittest.main()
