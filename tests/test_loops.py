import unittest
import os
import shutil
import tempfile
from pathlib import Path
from src.scanner import scan_directory
from src.mover import move_media_safe, STATUS_SKIPPED, STATUS_SUCCESS

class TestLoops(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.src = self.test_dir / "src"
        self.src.mkdir()
        
    def tearDown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass # Windows a veces bloquea borrados rápidos

    def test_symlink_loop(self):
        # Crear un symlink que apunte a sí mismo o al padre
        # En Windows requiere permisos de admin o modo desarrollador.
        # Si falla la creación del symlink, saltamos el test.
        try:
            os.symlink(self.src, self.src / "loop_link")
        except OSError:
            print("Skipping symlink test (No permission)")
            return

        # Poner un archivo dentro
        (self.src / "foto.jpg").touch()
        
        # Escanear. Si entra en loop, esto nunca terminará (timeout).
        # Como os.walk followlinks=False por defecto, debería ignorar 'loop_link'
        files = list(scan_directory(self.src))
        
        # Deberíamos ver 1 solo archivo (foto.jpg), no infinitos 'loop_link/foto.jpg'
        self.assertEqual(len(files), 1)

    def test_dest_inside_src(self):
        # Caso: Destino es una subcarpeta del Origen
        # src/
        #   foto.jpg
        #   organized/ (DESTINO)
        
        dest = self.src / "organized"
        dest.mkdir()
        
        photo = self.src / "foto.jpg"
        with open(photo, "wb") as f:
            f.write(b"DATA")
            
        # Ejecutar flujo MANUALMENTE (Scanner -> Mover) como haría el main loop
        # El problema potencial es:
        # 1. Scanner ve 'foto.jpg'
        # 2. Mover lo mueve a 'src/organized/202X/foto.jpg'
        # 3. Scanner entra en 'src/organized' y ve 'foto.jpg' (el movido)
        # 4. Mover intenta moverlo de nuevo... ¿Loop?
        
        # NOTA: scan_directory usa os.walk. os.walk genera la lista de dirs AL PRINCIPIO.
        # Si 'organized' ya existe (vacía), lo listará.
        # Cuando entre en 'organized', verá lo que haya EN ESE MOMENTO.
        # Si movemos el archivo ANTES de que el walk llegue ahí, lo verá.
        
        # Simulemos el Loop Principal
        scanner_gen = scan_directory(self.src)
        
        # Iteracion 1: Encuentra foto.jpg en root
        try:
            group1 = next(scanner_gen)
        except StopIteration:
            self.fail("No encontró la foto inicial")
            
        self.assertEqual(group1.main_file.name, "foto.jpg")
        
        # Movemos
        res1 = move_media_safe(group1, dest)
        self.assertEqual(res1.status, STATUS_SUCCESS) # Se mueve a organized/202X/...
        
        # Iteracion continua... ¿Encuentra la foto movida?
        # Depende de cuándo os.walk lea el directorio 'organized'.
        
        files_found_after = []
        for group in scanner_gen:
            files_found_after.append(group)
            # Si lo encuentra, intentamos moverlo
            res2 = move_media_safe(group, dest)
            
            # AQUÍ ES LA CLAVE: El check de Idempotencia debe decir SKIPPED
            # Si dice SUCCESS, lo movería dentro de sí mismo (organized/202X/organized/202X...) -> LOOP INFINITO
            
            if res2.status != STATUS_SKIPPED:
                self.fail(f"Loop detectado! Intentó mover un archivo ya organizado: {group.main_file}")
                
        # Si llegamos aquí sin fail, el test pasó.
        # Es posible que files_found_after esté vacío (si os.walk leyó organized cuando estaba vacío)
        # O tenga 1 elemento (si lo leyó después). Ambos casos son aceptables SI move_media_safe protege.

if __name__ == '__main__':
    unittest.main()
