import unittest
import shutil
import tempfile
from pathlib import Path
from src.mover import move_media_safe
from src.scanner import MediaGroup

class TestClassification(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.src_dir = self.test_dir / "src"
        self.dest_dir = self.test_dir / "dest"
        self.src_dir.mkdir()
        self.dest_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_classification_logic(self):
        # Create dummy files
        jpg_file = self.src_dir / "test.jpg"
        raw_file = self.src_dir / "test.arw"
        mp4_file = self.src_dir / "test.mp4"
        
        for f in [jpg_file, raw_file, mp4_file]:
            f.write_text("dummy")

        # Move JPG
        group_jpg = MediaGroup(jpg_file)
        res_jpg = move_media_safe(group_jpg, self.dest_dir, classify_by_type=True)
        self.assertIn("FOTOS", str(res_jpg.destination))
        self.assertTrue(res_jpg.destination.exists())

        # Move RAW
        group_raw = MediaGroup(raw_file)
        res_raw = move_media_safe(group_raw, self.dest_dir, classify_by_type=True)
        self.assertIn("RAW", str(res_raw.destination))
        self.assertTrue(res_raw.destination.exists())

        # Move MP4
        group_mp4 = MediaGroup(mp4_file)
        res_mp4 = move_media_safe(group_mp4, self.dest_dir, classify_by_type=True)
        self.assertIn("VIDEOS", str(res_mp4.destination))
        self.assertTrue(res_mp4.destination.exists())

if __name__ == '__main__':
    unittest.main()
