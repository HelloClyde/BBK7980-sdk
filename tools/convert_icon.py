"""Convert a PNG to a BBK7980 icon; optionally preview the visible 32x24 area."""
from pathlib import Path
import argparse

WIDTH = 32
VISIBLE_HEIGHT = 24
STORED_HEIGHT = 32
ICON_BYTES = WIDTH * STORED_HEIGHT // 4


def pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError('PNG icons/previews require Pillow: python -m pip install -r requirements-images.txt') from exc
    return Image, ImageOps


def png_icon(path):
    """Fit the whole picture inside the visible area; do not crop its bottom."""
    Image, ImageOps = pillow()
    with Image.open(path) as source:
        if source.format != 'PNG':
            raise ValueError('Expected a PNG image')
        rgba = ImageOps.exif_transpose(source).convert('RGBA')
        background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
        background.alpha_composite(rgba)
        gray = background.convert('L')
    fitted = ImageOps.contain(gray, (WIDTH, VISIBLE_HEIGHT), method=Image.Resampling.LANCZOS)
    canvas = Image.new('L', (WIDTH, STORED_HEIGHT), 255)
    canvas.paste(fitted, ((WIDTH - fitted.width) // 2, (VISIBLE_HEIGHT - fitted.height) // 2))
    # Nearest of white/light-gray/dark-gray/black; deterministic, no dithering.
    pixels = bytes((255 - value + 42) // 85 for value in canvas.tobytes())
    return bytes(sum(pixels[i + j] << (6 - 2 * j) for j in range(4))
                 for i in range(0, len(pixels), 4))


def load_icon(path):
    path = Path(path)
    if path.suffix.lower() == '.png':
        return png_icon(path)
    data = path.read_bytes()
    if len(data) != ICON_BYTES:
        raise ValueError('Raw icon must be 256 bytes (32x32, packed 2bpp); PNG input must use .png')
    return data


def save_preview(data, path):
    Image, _ = pillow()
    if len(data) != ICON_BYTES:
        raise ValueError('Icon must be 256 bytes')
    pixels = bytes(255 - ((value >> shift) & 3) * 85
                   for value in data[:WIDTH * VISIBLE_HEIGHT // 4]
                   for shift in (6, 4, 2, 0))
    image = Image.frombytes('L', (WIDTH, VISIBLE_HEIGHT), pixels)
    image.save(path, format='PNG')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='PNG image, or an existing 256-byte raw icon')
    parser.add_argument('-o', '--output', type=Path, help='Output .bin; defaults to INPUT with .bin suffix')
    parser.add_argument('--preview', type=Path, help='Also save a 32x24 grayscale PNG preview')
    args = parser.parse_args()
    output = args.output or args.input.with_suffix('.bin')
    paths = [args.input.resolve(), output.resolve()]
    if args.preview:
        paths.append(args.preview.resolve())
    if len(set(paths)) != len(paths):
        parser.error('Input, output and preview must be different files')
    try:
        data = load_icon(args.input)
        output.parent.mkdir(parents=True, exist_ok=True)
        if args.preview:
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            save_preview(data, args.preview)
        output.write_bytes(data)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'{output}: {len(data)} bytes; desktop visible area 32x24')
    if args.preview:
        print(f'Preview: {args.preview}')


if __name__ == '__main__':
    main()
