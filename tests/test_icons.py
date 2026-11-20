"""Check user-visible PNG sizing, transparency, tone levels and raw compatibility."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from convert_icon import load_icon, save_preview


class Icons(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def convert(self, image, filename='icon.png', **save_options):
        path = self.root/filename
        image.save(path, format='PNG', **save_options)
        return load_icon(path)

    def unpack(self, data):
        return bytes((value >> shift) & 3 for value in data for shift in (6, 4, 2, 0))

    def test_exact_four_shades_pack_high_bits_first_and_pad_bottom(self):
        image = Image.frombytes('L', (32, 24), bytes([255, 170, 85, 0]*192))
        self.assertEqual(self.convert(image), b'\x1b'*192 + b'\0'*64)

    def test_square_fits_inside_visible_area_without_cropping(self):
        pixels = self.unpack(self.convert(Image.new('RGB', (32, 32), 'black')))
        self.assertEqual(pixels, bytes(3 if y < 24 and 4 <= x < 28 else 0
                                      for y in range(32) for x in range(32)))

    def test_wide_image_keeps_aspect_and_centers_vertically(self):
        pixels = self.unpack(self.convert(Image.new('RGB', (64, 16), 'black')))
        self.assertEqual(pixels, bytes(3 if 8 <= y < 16 else 0
                                      for y in range(32) for x in range(32)))

    def test_rgba_transparency_is_white_and_partial_alpha_blends(self):
        image = Image.new('RGBA', (32, 24), (0, 0, 0, 0))
        image.putpixel((0, 0), (0, 0, 0, 255))
        image.putpixel((1, 0), (0, 0, 0, 128))
        pixels = self.unpack(self.convert(image))
        self.assertEqual(pixels[:4], bytes([3, 2, 0, 0]))
        self.assertFalse(any(pixels[4:]))

    def test_indexed_png_transparency_and_uppercase_suffix(self):
        image = Image.new('P', (32, 24), 0)
        image.putpalette([0, 0, 0, 0, 0, 0] + [0]*762)
        image.putpixel((0, 0), 1)
        pixels = self.unpack(self.convert(image, 'icon.PNG', transparency=0))
        self.assertEqual(pixels[0], 3)
        self.assertFalse(any(pixels[1:]))

    def test_rgb_colors_use_luminance(self):
        image = Image.new('RGB', (32, 24), 'white')
        for x, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]): image.putpixel((x, 0), color)
        self.assertEqual(self.unpack(self.convert(image))[:4], bytes([2, 1, 3, 0]))

    def test_raw_icon_needs_no_pillow_and_preserves_all_bytes(self):
        raw = bytes(range(256))
        path = self.root/'icon.bin'
        path.write_bytes(raw)
        original_import = __import__
        def no_pillow(name, *args, **kwargs):
            if name == 'PIL' or name.startswith('PIL.'): raise ImportError('Pillow unavailable')
            return original_import(name, *args, **kwargs)
        with mock.patch('builtins.__import__', side_effect=no_pillow):
            self.assertEqual(load_icon(path), raw)

    def test_invalid_raw_length_and_corrupt_png_are_rejected(self):
        path = self.root/'bad.bin';path.write_bytes(b'\0'*192)
        with self.assertRaises(ValueError): load_icon(path)
        path = self.root/'bad.png';path.write_bytes(b'not a PNG')
        with self.assertRaises(OSError): load_icon(path)

    def test_preview_contains_only_visible_area_and_four_levels(self):
        data = b'\x1b'*192 + b'\xff'*64
        path = self.root/'preview.png';save_preview(data, path)
        with Image.open(path) as preview:
            self.assertEqual(preview.size, (32, 24))
            self.assertEqual(preview.tobytes(), bytes([255, 170, 85, 0]*192))

    def test_cli_default_output_preview_and_input_protection(self):
        path = self.root/'icon.png';Image.new('L', (32, 24), 0).save(path)
        preview = self.root/'previews/preview.png'
        command = [sys.executable, str(ROOT/'tools/convert_icon.py'), str(path)]
        subprocess.run([*command, '--preview', str(preview)], check=True, capture_output=True)
        self.assertEqual(path.with_suffix('.bin').read_bytes(), b'\xff'*192 + b'\0'*64)
        self.assertTrue(preview.is_file())
        output = self.root/'nested/icon.bin'
        subprocess.run([*command, '-o', str(output)], check=True, capture_output=True)
        self.assertEqual(output.read_bytes(), path.with_suffix('.bin').read_bytes())
        original = path.read_bytes()
        result = subprocess.run([*command, '-o', str(path)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
