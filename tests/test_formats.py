import unittest
from pathlib import Path
from src.scanner import ALL_MEDIA_EXTENSIONS, SIDECAR_EXTENSIONS, scan_directory
from src.date_extractor import get_date_taken
import shutil
import tempfile
import os
from datetime import datetime

class TestSpecificFormats(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_dummy_file(self, filename):
        path = self.root / filename
        with open(path, 'wb') as f:
            f.write(b'dummy content')
        return path

    def test_extensions_are_defined(self):
        """Verify that requested extensions are in the allowlists"""
        self.assertIn('.heic', ALL_MEDIA_EXTENSIONS)
        self.assertIn('.mov', ALL_MEDIA_EXTENSIONS)
        self.assertIn('.aae', SIDECAR_EXTENSIONS)

    def test_scanner_detects_formats(self):
        """Verify scanner picks up heic, mov and associates aae"""
        self.create_dummy_file("photo.heic")
        self.create_dummy_file("photo.aae")
        self.create_dummy_file("video.mov")
        
        groups = list(scan_directory(self.root))
        
        # Should find 2 groups: photo.heic (with sidecar) and video.mov
        self.assertEqual(len(groups), 2)
        
        heic_group = next(g for g in groups if g.main_file.suffix == '.heic')
        self.assertEqual(heic_group.main_file.name, "photo.heic")
        self.assertEqual(len(heic_group.sidecars), 1)
        self.assertEqual(heic_group.sidecars[0].name, "photo.aae")

        mov_group = next(g for g in groups if g.main_file.suffix == '.mov')
        self.assertEqual(mov_group.main_file.name, "video.mov")

    def test_date_extractor_fallback(self):
        """Verify date extractor doesn't crash on dummy heic/mov and falls back to fs date"""
        p_heic = self.create_dummy_file("test.heic")
        p_mov = self.create_dummy_file("test.mov")
        
        date_heic = get_date_taken(p_heic)
        date_mov = get_date_taken(p_mov)
        
        self.assertIsInstance(date_heic, datetime)
        self.assertIsInstance(date_mov, datetime)

if __name__ == '__main__':
    unittest.main()
