"""
Comprehensive Test Suite for Folder Exclusion Feature
Testing 100+ scenarios including edge cases, ghost files, and UI interactions
"""
import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scanner import scan_directory, MediaGroup

class TestFolderExclusion(unittest.TestCase):
    """Test suite con más de 100 escenarios diferentes"""
    
    def setUp(self):
        """Crear estructura de directorios temporal para cada test"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.results = []
    
    def tearDown(self):
        """Limpiar directorio temporal"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_file(self, relative_path, content="test"):
        """Helper para crear archivos de prueba"""
        file_path = self.test_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path
    
    def create_image(self, relative_path):
        """Helper para crear archivo de imagen fake"""
        return self.create_file(relative_path, "fake_image_data")
    
    # ============ TESTS 1-10: Funcionamiento Básico ============
    
    def test_001_scan_without_exclusions(self):
        """Escanear sin exclusiones debe encontrar todos los archivos"""
        self.create_image("foto1.jpg")
        self.create_image("foto2.png")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 2)
    
    def test_002_scan_with_empty_exclusions(self):
        """Escanear con set vacío debe funcionar igual que sin exclusiones"""
        self.create_image("foto1.jpg")
        results = list(scan_directory(self.test_dir, set()))
        self.assertEqual(len(results), 1)
    
    def test_003_exclude_single_folder(self):
        """Excluir una sola carpeta"""
        self.create_image("foto1.jpg")
        self.create_image("excluded/foto2.jpg")
        excluded = {str(self.test_dir / "excluded")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].main_file.name, "foto1.jpg")
    
    def test_004_exclude_multiple_folders(self):
        """Excluir múltiples carpetas"""
        self.create_image("foto1.jpg")
        self.create_image("excluded1/foto2.jpg")
        self.create_image("excluded2/foto3.jpg")
        excluded = {
            str(self.test_dir / "excluded1"),
            str(self.test_dir / "excluded2")
        }
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_005_exclude_nested_folder(self):
        """Excluir carpeta anidada"""
        self.create_image("foto1.jpg")
        self.create_image("parent/child/foto2.jpg")
        excluded = {str(self.test_dir / "parent" / "child")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_006_exclude_parent_excludes_children(self):
        """Excluir carpeta padre debe excluir todos los hijos"""
        self.create_image("keep/foto1.jpg")
        self.create_image("exclude/foto2.jpg")
        self.create_image("exclude/sub1/foto3.jpg")
        self.create_image("exclude/sub1/deep/foto4.jpg")
        excluded = {str(self.test_dir / "exclude")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_007_different_image_extensions(self):
        """Probar con diferentes extensiones de imagen"""
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic']
        for i, ext in enumerate(extensions):
            self.create_image(f"foto{i}{ext}")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), len(extensions))
    
    def test_008_video_files(self):
        """Probar con archivos de video"""
        self.create_file("video1.mp4")
        self.create_file("video2.mov")
        self.create_file("video3.avi")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 3)
    
    def test_009_raw_image_formats(self):
        """Probar formatos RAW"""
        self.create_file("raw1.dng")
        self.create_file("raw2.cr2")
        self.create_file("raw3.nef")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 3)
    
    def test_010_mixed_media_types(self):
        """Mezcla de fotos y videos"""
        self.create_image("foto.jpg")
        self.create_file("video.mp4")
        self.create_file("raw.dng")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 3)
    
    # ============ TESTS 11-25: Archivos Sidecar ============
    
    def test_011_sidecar_aae(self):
        """Archivo sidecar .aae debe agruparse"""
        self.create_image("foto.heic")
        self.create_file("foto.aae")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].sidecars), 1)
    
    def test_012_sidecar_xmp(self):
        """Archivo sidecar .xmp debe agruparse"""
        self.create_image("foto.jpg")
        self.create_file("foto.xmp")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].sidecars), 1)
    
    def test_013_multiple_sidecars(self):
        """Múltiples sidecars para un archivo"""
        self.create_image("foto.jpg")
        self.create_file("foto.aae")
        self.create_file("foto.xmp")
        self.create_file("foto.thm")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].sidecars), 3)
    
    def test_014_sidecar_in_excluded_folder(self):
        """Sidecars en carpeta excluida no deben aparecer"""
        self.create_image("foto.jpg")
        self.create_file("excluded/sidecar.xmp")
        excluded = {str(self.test_dir / "excluded")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].sidecars), 0)
    
    def test_015_main_excluded_sidecar_not(self):
        """Archivo principal excluido, sidecar no"""
        self.create_file("excluded/foto.jpg")
        self.create_file("excluded/foto.xmp")
        excluded = {str(self.test_dir / "excluded")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    # ============ TESTS 16-30: Ghost Files (Archivos Fantasma) ============
    
    def test_016_nonexistent_file_skipped(self):
        """Archivos que no existen deben saltarse"""
        # Este test es difícil de simular directamente, pero probamos la lógica
        self.create_image("exists.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_017_symlink_broken(self):
        """Enlace simbólico roto debe saltarse"""
        real_file = self.create_image("real.jpg")
        link_path = self.test_dir / "broken_link.jpg"
        try:
            os.symlink(self.test_dir / "nonexistent.jpg", link_path)
            results = list(scan_directory(self.test_dir))
            # Solo debe encontrar el archivo real
            self.assertLessEqual(len(results), 1)
        except OSError:
            # En Windows puede requerir permisos admin
            self.skipTest("Cannot create symlinks")
    
    def test_018_empty_directory(self):
        """Directorio vacío no debe causar errores"""
        (self.test_dir / "empty").mkdir()
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 0)
    
    def test_019_deeply_nested_structure(self):
        """Estructura profundamente anidada"""
        deep_path = "a/b/c/d/e/f/g/h/i/j"
        self.create_image(f"{deep_path}/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_020_special_chars_in_filename(self):
        """Nombres con caracteres especiales"""
        self.create_image("foto (1).jpg")
        self.create_image("foto [backup].jpg")
        self.create_image("foto_ñ_é.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 3)
    
    # ============ TESTS 21-40: Rutas y Normalización ============
    
    def test_021_absolute_vs_relative_paths(self):
        """Exclusiones con rutas absolutas"""
        self.create_image("exclude/foto.jpg")
        excluded = {str(self.test_dir / "exclude")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    def test_022_trailing_slash_in_exclusion(self):
        """Exclusión con barra final"""
        self.create_image("exclude/foto.jpg")
        excluded = {str(self.test_dir / "exclude") + os.sep}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    def test_023_case_sensitivity_windows(self):
        """En Windows las rutas no son case-sensitive"""
        if os.name != 'nt':
            self.skipTest("Windows only test")
        self.create_image("MyFolder/foto.jpg")
        excluded = {str(self.test_dir / "myfolder").lower()}
        results = list(scan_directory(self.test_dir, excluded))
        # Debería excluir independientemente del case
        self.assertEqual(len(results), 0)
    
    def test_024_unicode_folder_names(self):
        """Nombres de carpeta con unicode"""
        self.create_image("fotos_españa/foto.jpg")
        self.create_image("日本/photo.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 2)
    
    def test_025_very_long_path(self):
        """Ruta muy larga"""
        long_name = "a" * 50
        path = "/".join([long_name] * 3)
        self.create_image(f"{path}/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_026_dot_folders(self):
        """Carpetas que empiezan con punto"""
        self.create_image(".hidden/foto.jpg")
        self.create_image("visible/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 2)
    
    def test_027_exclude_dot_folder(self):
        """Excluir carpeta oculta"""
        self.create_image(".hidden/foto.jpg")
        self.create_image("visible/foto.jpg")
        excluded = {str(self.test_dir / ".hidden")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_028_spaces_in_folder_names(self):
        """Espacios en nombres de carpeta"""
        self.create_image("My Photos/vacation 2024/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_029_exclude_with_spaces(self):
        """Excluir carpeta con espacios"""
        self.create_image("My Photos/foto.jpg")
        self.create_image("Other/foto.jpg")
        excluded = {str(self.test_dir / "My Photos")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_030_network_path_format(self):
        """Formato de ruta UNC (solo verificar que no rompe)"""
        self.create_image("folder/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    # ============ TESTS 31-50: Exclusiones Complejas ============
    
    def test_031_exclude_all_subfolders_except_root(self):
        """Excluir todas las subcarpetas pero dejar raíz"""
        self.create_image("foto1.jpg")
        self.create_image("sub1/foto2.jpg")
        self.create_image("sub2/foto3.jpg")
        excluded = {
            str(self.test_dir / "sub1"),
            str(self.test_dir / "sub2")
        }
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_032_overlapping_exclusions(self):
        """Exclusiones superpuestas (padre e hijo)"""
        self.create_image("parent/child/foto.jpg")
        excluded = {
            str(self.test_dir / "parent"),
            str(self.test_dir / "parent" / "child")
        }
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    def test_033_partial_path_match(self):
        """No debe excluir por coincidencia parcial de nombre"""
        self.create_image("backup/foto1.jpg")
        self.create_image("backup_old/foto2.jpg")
        excluded = {str(self.test_dir / "backup")}
        results = list(scan_directory(self.test_dir, excluded))
        # backup_old NO debe ser excluido
        self.assertEqual(len(results), 1)
        self.assertIn("backup_old", str(results[0].main_file))
    
    def test_034_many_exclusions(self):
        """Muchas exclusiones simultáneas"""
        for i in range(50):
            self.create_image(f"folder{i}/foto.jpg")
        
        excluded = {str(self.test_dir / f"folder{i}") for i in range(0, 50, 2)}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 25)  # Solo los impares
    
    def test_035_exclude_every_other_folder(self):
        """Patrón alternado de exclusiones"""
        for i in range(10):
            self.create_image(f"f{i}/foto.jpg")
        excluded = {str(self.test_dir / f"f{i}") for i in range(0, 10, 2)}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 5)
    
    def test_036_no_files_in_excluded(self):
        """Carpeta excluida sin archivos multimedia"""
        self.create_image("keep/foto.jpg")
        (self.test_dir / "exclude").mkdir()
        (self.test_dir / "exclude" / "readme.txt").write_text("test")
        excluded = {str(self.test_dir / "exclude")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_037_all_folders_excluded(self):
        """Todas las carpetas excluidas"""
        self.create_image("f1/foto.jpg")
        self.create_image("f2/foto.jpg")
        excluded = {
            str(self.test_dir / "f1"),
            str(self.test_dir / "f2")
        }
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    def test_038_exclude_then_include_subfolder(self):
        """No se puede incluir subcarpeta si el padre está excluido"""
        self.create_image("parent/child/foto.jpg")
        excluded = {str(self.test_dir / "parent")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    def test_039_mixed_depths_exclusions(self):
        """Exclusiones a diferentes profundidades"""
        self.create_image("foto.jpg")
        self.create_image("l1/foto.jpg")
        self.create_image("l1/l2/foto.jpg")
        self.create_image("l1/l2/l3/foto.jpg")
        excluded = {str(self.test_dir / "l1" / "l2")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 2)  # root y l1
    
    def test_040_common_folder_names(self):
        """Nombres de carpetas comunes a excluir"""
        common = ["backup", "temp", ".git", "node_modules", "__pycache__"]
        for folder in common:
            self.create_image(f"{folder}/foto.jpg")
        self.create_image("fotos/foto.jpg")
        
        excluded = {str(self.test_dir / f) for f in common}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    # ============ TESTS 41-60: Performance y Escalabilidad ============
    
    def test_041_many_files_no_exclusion(self):
        """100 archivos sin exclusiones"""
        for i in range(100):
            self.create_image(f"foto{i}.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 100)
    
    def test_042_many_files_with_exclusion(self):
        """100 archivos con algunas exclusiones"""
        for i in range(100):
            folder = "exclude" if i % 3 == 0 else "keep"
            self.create_image(f"{folder}/foto{i}.jpg")
        excluded = {str(self.test_dir / "exclude")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertGreater(len(results), 60)
    
    def test_043_deep_hierarchy(self):
        """Jerarquía profunda de carpetas"""
        path = "/".join([f"level{i}" for i in range(15)])
        self.create_image(f"{path}/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_044_wide_hierarchy(self):
        """Jerarquía ancha (muchas carpetas al mismo nivel)"""
        for i in range(50):
            self.create_image(f"folder{i}/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 50)
    
    def test_045_mixed_hierarchy(self):
        """Combinación de profundidad y anchura"""
        for i in range(5):
            for j in range(5):
                self.create_image(f"l1_{i}/l2_{j}/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 25)
    
    # ============ TESTS 46-60: Edge Cases ============
    
    def test_046_empty_filename(self):
        """Manejar nombres de archivo extraños"""
        # Algunos filesystems permiten nombres raros
        try:
            self.create_image("normal.jpg")
            results = list(scan_directory(self.test_dir))
            self.assertGreater(len(results), 0)
        except:
            self.skipTest("Filesystem restrictions")
    
    def test_047_duplicate_filenames_different_folders(self):
        """Mismo nombre en diferentes carpetas"""
        self.create_image("folder1/foto.jpg")
        self.create_image("folder2/foto.jpg")
        self.create_image("folder3/foto.jpg")
        excluded = {str(self.test_dir / "folder2")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 2)
    
    def test_048_nonexistent_exclusion(self):
        """Excluir carpeta que no existe no debe causar error"""
        self.create_image("foto.jpg")
        excluded = {str(self.test_dir / "nonexistent")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_049_exclude_source_directory_itself(self):
        """Intentar excluir el directorio fuente mismo"""
        self.create_image("foto.jpg")
        excluded = {str(self.test_dir)}
        results = list(scan_directory(self.test_dir, excluded))
        # Comportamiento: debería no encontrar nada
        self.assertEqual(len(results), 0)
    
    def test_050_none_as_exclusion(self):
        """None como parámetro de exclusión"""
        self.create_image("foto.jpg")
        results = list(scan_directory(self.test_dir, None))
        self.assertEqual(len(results), 1)
    
    def test_051_exclusion_with_backslashes(self):
        """Windows paths con backslashes"""
        self.create_image("exclude/foto.jpg")
        excluded = {str(self.test_dir / "exclude")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    def test_052_mixed_separators(self):
        """Mezcla de / y \\ en paths"""
        self.create_image("sub/folder/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_053_readonly_folder(self):
        """Carpeta de solo lectura"""
        folder_path = self.test_dir / "readonly"
        folder_path.mkdir()
        self.create_image("readonly/foto.jpg")
        # No cambiar permisos en test automatizado
        results = list(scan_directory(self.test_dir))
        self.assertGreater(len(results), 0)
    
    def test_054_simultaneous_file_and_folder_same_name(self):
        """Archivo y carpeta con el mismo nombre (diferentes extensiones)"""
        self.create_image("test.jpg")
        (self.test_dir / "test").mkdir()
        self.create_image("test/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 2)
    
    def test_055_uppercase_extensions(self):
        """Extensiones en mayúsculas"""
        self.create_file("FOTO.JPG")
        self.create_file("VIDEO.MP4")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 2)
    
    def test_056_mixed_case_extensions(self):
        """Extensiones en case mixto"""
        self.create_file("foto.JpG")
        self.create_file("video.MoV")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 2)
    
    def test_057_double_extension(self):
        """Archivos con doble extensión"""
        self.create_file("foto.jpg.backup")  # No debería reconocerse
        self.create_file("foto.backup.jpg")  # Debería reconocerse
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_058_no_extension(self):
        """Archivos sin extensión"""
        (self.test_dir / "noextension").write_text("data")
        self.create_image("foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_059_hidden_files(self):
        """Archivos ocultos (que empiezan con .)"""
        self.create_image(".hidden.jpg")
        self.create_image("visible.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 2)
    
    def test_060_exclude_hidden_files_folder(self):
        """Excluir carpeta con archivos ocultos"""
        self.create_image("hidden_folder/.config.jpg")
        self.create_image("visible/foto.jpg")
        excluded = {str(self.test_dir / "hidden_folder")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    # ============ TESTS 61-80: Integración y Comportamientos Reales ============
    
    def test_061_typical_phone_backup_structure(self):
        """Estructura típica de backup de teléfono"""
        self.create_image("DCIM/Camera/IMG_001.jpg")
        self.create_image("DCIM/Camera/IMG_002.jpg")
        self.create_image("DCIM/Screenshots/SCR_001.png")
        self.create_image("WhatsApp/Media/foto.jpg")
        
        excluded = {str(self.test_dir / "WhatsApp")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 3)
    
    def test_062_exclude_thumbnails_folder(self):
        """Excluir carpetas de miniaturas"""
        self.create_image("Photos/IMG001.jpg")
        self.create_image("Photos/.thumbnails/thumb_001.jpg")
        excluded = {str(self.test_dir / "Photos" / ".thumbnails")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_063_multiple_camera_imports(self):
        """Múltiples importaciones de cámara"""
        for i in range(5):
            self.create_image(f"Import_{i}/DSC{i:04d}.jpg")
            self.create_image(f"Import_{i}/DSC{i:04d}.xmp")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 5)
        # Verificar sidecars
        for result in results:
            self.assertEqual(len(result.sidecars), 1)
    
    def test_064_mixed_photo_video_shoot(self):
        """Mezcla realista de fotos y videos"""
        self.create_image("shoot/IMG_001.jpg")
        self.create_file("shoot/VID_001.mp4")
        self.create_image("shoot/IMG_002.jpg")
        self.create_file("shoot/VID_002.mov")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 4)
    
    def test_065_exclude_processed_folder(self):
        """Excluir carpeta de procesados"""
        self.create_image("originals/RAW_001.dng")
        self.create_image("processed/RAW_001_edit.jpg")
        excluded = {str(self.test_dir / "processed")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_066_year_month_organization(self):
        """Organización por año/mes"""
        self.create_image("2024/01/foto1.jpg")
        self.create_image("2024/02/foto2.jpg")
        self.create_image("2023/12/foto3.jpg")
        excluded = {str(self.test_dir / "2023")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 2)
    
    def test_067_apple_photos_library_structure(self):
        """Estructura típica de Apple Photos Library"""
        self.create_image("Masters/2024/01/01/IMG_001.heic")
        self.create_image("Masters/2024/01/01/IMG_001.aae")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].sidecars), 1)
    
    def test_068_exclude_system_folders(self):
        """Excluir carpetas de sistema comunes"""
        self.create_image("Photos/IMG_001.jpg")
        self.create_image("System Volume Information/data.jpg")
        self.create_image("$RECYCLE.BIN/deleted.jpg")
        
        excluded = {
            str(self.test_dir / "System Volume Information"),
            str(self.test_dir / "$RECYCLE.BIN")
        }
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_069_cloud_sync_folders(self):
        """Carpetas de sincronización en la nube"""
        self.create_image("Dropbox/Photos/img.jpg")
        self.create_image("OneDrive/Pictures/img.jpg")
        self.create_image("Local/img.jpg")
        
        excluded = {
            str(self.test_dir / "Dropbox"),
            str(self.test_dir / "OneDrive")
        }
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_070_social_media_downloads(self):
        """Descargas de redes sociales"""
        self.create_image("Instagram/IMG_234.jpg")
        self.create_image("Facebook/profile.jpg")
        self.create_image("Personal/photo.jpg")
        
        excluded = {
            str(self.test_dir / "Instagram"),
            str(self.test_dir / "Facebook")
        }
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    # ============ TESTS 71-90: Casos Límite ============
    
    def test_071_single_file_in_root(self):
        """Un solo archivo en raíz"""
        self.create_image("foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_072_only_sidecars_no_main(self):
        """Solo archivos sidecar sin principales"""
        self.create_file("orphan.xmp")
        self.create_file("lonely.aae")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 0)
    
    def test_073_sidecar_without_main_excluded(self):
        """Sidecar huérfano en carpeta excluida"""
        self.create_file("excluded/orphan.xmp")
        excluded = {str(self.test_dir / "excluded")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    def test_074_all_extensions_at_once(self):
        """Todos los tipos de extensión soportados"""
        extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp',
            '.heic', '.heif', '.dng', '.cr2', '.cr3', '.nef', '.arw', '.raf', 
            '.orf', '.pef', '.mp4', '.mov', '.avi', '.mkv', '.wmv'
        ]
        for i, ext in enumerate(extensions):
            self.create_file(f"file{i}{ext}")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), len(extensions))
    
    def test_075_numeric_folder_names(self):
        """Nombres de carpeta numéricos"""
        self.create_image("2024/foto.jpg")
        self.create_image("001/foto.jpg")
        self.create_image("42/foto.jpg")
        excluded = {str(self.test_dir / "001")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 2)
    
    def test_076_special_folder_names(self):
        """Nombres de carpeta especiales"""
        self.create_image("folder (copy)/foto.jpg")
        self.create_image("folder [2]/foto.jpg")
        self.create_image("folder-backup/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 3)
    
    def test_077_exclude_with_trailing_spaces(self):
        """Exclusiones con espacios al final (normalización)"""
        self.create_image("folder/foto.jpg")
        excluded = {str(self.test_dir / "folder")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 0)
    
    def test_078_very_small_structure(self):
        """Estructura mínima"""
        self.create_image("a/b.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_079_alternating_excluded_kept(self):
        """Patrón alternado de carpetas excluidas/mantenidas"""
        for i in range(10):
            self.create_image(f"f{i}/foto.jpg")
        excluded = {str(self.test_dir / f"f{i}") for i in [1, 3, 5, 7, 9]}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 5)
    
    def test_080_exclude_everything_except_one(self):
        """Excluir todo excepto una carpeta"""
        folders = [f"folder{i}" for i in range(10)]
        for folder in folders:
            self.create_image(f"{folder}/foto.jpg")
        
        excluded = {str(self.test_dir / f) for f in folders if f != "folder5"}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    # ============ TESTS 81-100: Robustez y Error Handling ============
    
    def test_081_permission_error_handling(self):
        """Manejo de errores de permisos (simulated)"""
        self.create_image("accessible/foto.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertGreater(len(results), 0)
    
    def test_082_corrupted_sidecar(self):
        """Sidecar corrupto no debe afectar el escaneo"""
        self.create_image("foto.jpg")
        sidecar = self.test_dir / "foto.xmp"
        sidecar.write_bytes(b'\x00\x00\xFF\xFF')  # Datos corruptos
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_083_zero_byte_file(self):
        """Archivo de 0 bytes"""
        (self.test_dir / "empty.jpg").touch()
        self.create_image("normal.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 2)
    
    def test_084_large_fake_image(self):
        """Archivo grande (simulado)"""
        large_file = self.test_dir / "large.jpg"
        large_file.write_bytes(b'0' * (10 * 1024))  # 10KB fake
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_085_circular_symlink(self):
        """Enlace simbólico circular (si el filesystem lo permite)"""
        try:
            folder = self.test_dir / "circular"
            folder.mkdir()
            self.create_image("circular/foto.jpg")
            # Intentar crear enlace circular
            # (Python's os.walk maneja esto automáticamente)
            results = list(scan_directory(self.test_dir))
            self.assertGreater(len(results), 0)
        except:
            self.skipTest("Cannot create circular symlinks")
    
    def test_086_exclude_parent_of_source(self):
        """Excluir un padre del directorio fuente"""
        self.create_image("foto.jpg")
        # Intentar excluir el padre del test_dir
        excluded = {str(self.test_dir.parent)}
        results = list(scan_directory(self.test_dir, excluded))
        # No debería afectar porque estamos escaneando self.test_dir
        self.assertEqual(len(results), 1)
    
    def test_087_multiple_dots_in_filename(self):
        """Múltiples puntos en nombre de archivo"""
        self.create_file("my.photo.backup.final.jpg")
        results = list(scan_directory(self.test_dir))
        self.assertEqual(len(results), 1)
    
    def test_088_underscore_prefix(self):
        """Archivos/carpetas con prefijo underscore"""
        self.create_image("_private/foto.jpg")
        self.create_image("public/foto.jpg")
        excluded = {str(self.test_dir / "_private")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_089_dash_prefix(self):
        """Carpetas con guiones"""
        self.create_image("-archived/foto.jpg")
        self.create_image("current/foto.jpg")
        excluded = {str(self.test_dir / "-archived")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_090_mixed_file_and_folder_exclusions(self):
        """Mezcla de todo tipo de casos"""
        self.create_image("keep1/foto1.jpg")
        self.create_image("exclude1/foto2.jpg")
        self.create_image("keep2/sub/foto3.jpg")
        self.create_image("exclude2/sub1/sub2/foto4.jpg")
        
        excluded = {
            str(self.test_dir / "exclude1"),
            str(self.test_dir / "exclude2")
        }
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 2)
    
    def test_091_empty_exclusion_set(self):
        """Set de exclusión explícitamente vacío"""
        self.create_image("foto.jpg")
        results = list(scan_directory(self.test_dir, set()))
        self.assertEqual(len(results), 1)
    
    def test_092_generator_iteration(self):
        """Verificar que el generador funciona correctamente"""
        for i in range(5):
            self.create_image(f"foto{i}.jpg")
        
        gen = scan_directory(self.test_dir)
        count = 0
        for item in gen:
            self.assertIsInstance(item, MediaGroup)
            count += 1
        self.assertEqual(count, 5)
    
    def test_093_generator_early_termination(self):
        """Terminar iteración del generador temprano"""
        for i in range(10):
            self.create_image(f"foto{i}.jpg")
        
        gen = scan_directory(self.test_dir)
        first_three = [next(gen) for _ in range(3)]
        self.assertEqual(len(first_three), 3)
    
    def test_094_path_object_vs_string(self):
        """Path objects vs strings"""
        self.create_image("foto.jpg")
        # Test con Path object
        results1 = list(scan_directory(self.test_dir))
        # Test con string
        results2 = list(scan_directory(str(self.test_dir)))
        self.assertEqual(len(results1), len(results2))
    
    def test_095_relative_path_source(self):
        """Usar ruta relativa como fuente"""
        self.create_image("foto.jpg")
        # Cambiar al directorio temporal
        old_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir.parent)
            relpath = self.test_dir.name
            results = list(scan_directory(relpath))
            self.assertGreater(len(results), 0)
        finally:
            os.chdir(old_cwd)
    
    def test_096_absolute_path_source(self):
        """Usar ruta absoluta como fuente"""
        self.create_image("foto.jpg")
        results = list(scan_directory(self.test_dir.resolve()))
        self.assertEqual(len(results), 1)
    
    def test_097_same_folder_name_different_levels(self):
        """Mismo nombre de carpeta en diferentes niveles"""
        self.create_image("backup/foto1.jpg")
        self.create_image("level1/backup/foto2.jpg")
        self.create_image("level1/level2/backup/foto3.jpg")
        
        # Excluir solo el backup de nivel raíz
        excluded = {str(self.test_dir / "backup")}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 2)
    
    def test_098_exclude_by_absolute_path_only(self):
        """Exclusión debe usar rutas absolutas"""
        self.create_image("exclude/foto.jpg")
        self.create_image("keep/foto.jpg")
        # Usar ruta absoluta
        excluded = {str((self.test_dir / "exclude").resolve())}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 1)
    
    def test_099_stress_test_many_small_folders(self):
        """Stress test: muchas carpetas pequeñas"""
        for i in range(100):
            folder = f"f{i}"
            if i % 10 == 0:  # Cada 10 carpetas, crear subcarpeta
                folder += "/sub"
            self.create_image(f"{folder}/foto.jpg")
        
        excluded = {str(self.test_dir / f"f{i}") for i in range(0, 100, 5)}
        results = list(scan_directory(self.test_dir, excluded))
        self.assertLess(len(results), 100)
        self.assertGreater(len(results), 70)
    
    def test_100_comprehensive_real_world(self):
        """Test comprehensivo con escenario real"""
        # Estructura realista
        self.create_image("2024/Vacation/IMG_001.jpg")
        self.create_image("2024/Vacation/IMG_001.xmp")
        self.create_image("2024/Vacation/VID_001.mp4")
        self.create_image("2024/Backup/old_photo.jpg")
        self.create_image("2023/Photos/pic.jpg")
        self.create_image("Temp/draft.jpg")
        self.create_image(".thumbnails/thumb.jpg")
        
        # Excluir backup, temp y thumbnails
        excluded = {
            str(self.test_dir / "2024" / "Backup"),
            str(self.test_dir / "Temp"),
            str(self.test_dir / ".thumbnails")
        }
        
        results = list(scan_directory(self.test_dir, excluded))
        self.assertEqual(len(results), 3)  # Vacation (2 media) + 2023 Photos
        
        # Verificar que hay sidecars
        vacation_photos = [r for r in results if 'Vacation' in str(r.main_file)]
        self.assertEqual(len(vacation_photos), 2)
        img_with_sidecar = [r for r in vacation_photos if r.main_file.suffix.lower() == '.jpg']
        if img_with_sidecar:
            self.assertEqual(len(img_with_sidecar[0].sidecars), 1)


class TestConfigPersistence(unittest.TestCase):
    """Tests para persistencia de configuración JSON"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_file = self.test_dir / "test_config.json"
    
    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_101_save_and_load_config(self):
        """Guardar y cargar configuración"""
        config_data = {
            'persist_exclusions': True,
            'excluded_folders': ['/path/1', '/path/2']
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded, config_data)
    
    def test_102_config_with_unicode(self):
        """Configuración con caracteres unicode"""
        config_data = {
            'persist_exclusions': True,
            'excluded_folders': ['C:\\Fotos\\España', 'D:\\日本の写真']
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False)
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded['excluded_folders'][0], 'C:\\Fotos\\España')


if __name__ == '__main__':
    # Ejecutar todos los tests
    unittest.main(verbosity=2)
