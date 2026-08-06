"""
Script para generar íconos PNG de la PWA.
Ejecutar una sola vez: python generate_icons.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'img')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BLUE = (13, 110, 253)      # #0d6efd
WHITE = (255, 255, 255)

for size in SIZES:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fondo circular azul
    margin = int(size * 0.05)
    draw.ellipse([margin, margin, size - margin, size - margin], fill=BLUE)

    # Letra "A" centrada en blanco
    font_size = int(size * 0.45)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except Exception:
        font = ImageFont.load_default()

    text = 'A'
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) / 2 - bbox[0]
    y = (size - text_h) / 2 - bbox[1]
    draw.text((x, y), text, fill=WHITE, font=font)

    path = os.path.join(OUTPUT_DIR, f'icon-{size}.png')
    img.save(path, 'PNG')
    print(f'Generado: {path}')

print('¡Íconos generados exitosamente!')
