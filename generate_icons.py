"""
Script para generar íconos PNG de la PWA — ATS Recluta
Diseño: fondo degradado azul, silueta de persona con carpeta + texto "ATS"
Ejecutar una sola vez: python generate_icons.py
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'img')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BLUE_DARK  = (10, 88, 202)   # #0a58ca
BLUE_MAIN  = (13, 110, 253)  # #0d6efd
WHITE      = (255, 255, 255, 255)
WHITE_SEMI = (255, 255, 255, 200)


def draw_rounded_rect(draw, xy, radius, fill):
    """Dibuja un rectángulo redondeado."""
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + 2*radius, y0 + 2*radius], fill=fill)
    draw.ellipse([x1 - 2*radius, y0, x1, y0 + 2*radius], fill=fill)
    draw.ellipse([x0, y1 - 2*radius, x0 + 2*radius, y1], fill=fill)
    draw.ellipse([x1 - 2*radius, y1 - 2*radius, x1, y1], fill=fill)


def generate_icon(size):
    s = size
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Fondo redondeado con degradado simulado ──
    radius = int(s * 0.18)
    draw_rounded_rect(draw, [0, 0, s-1, s-1], radius, BLUE_DARK)
    # Capa superior más clara para simular degradado
    overlay = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    draw_rounded_rect(od, [0, 0, s-1, int(s*0.5)], radius, (13, 110, 253, 100))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # ── Figura humana (cabeza + cuerpo) ──
    cx = s * 0.38   # centro horizontal de la figura
    # Cabeza
    hr = s * 0.09
    hy = s * 0.22
    draw.ellipse([cx-hr, hy-hr, cx+hr, hy+hr], fill=WHITE)
    # Cuerpo (trapecio invertido = hombros)
    bx0 = cx - s*0.13
    bx1 = cx + s*0.13
    by0 = hy + hr + s*0.02
    by1 = by0 + s*0.17
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=int(s*0.03), fill=WHITE)

    # ── Carpeta/documento (lado derecho) ──
    fx = s * 0.62
    fy = s * 0.20
    fw = s * 0.22
    fh = s * 0.28
    # Cuerpo de la carpeta
    draw.rounded_rectangle([fx, fy + fh*0.12, fx+fw, fy+fh],
                            radius=int(s*0.025), fill=WHITE_SEMI)
    # Pestaña superior
    draw.rounded_rectangle([fx, fy, fx + fw*0.55, fy + fh*0.15],
                            radius=int(s*0.02), fill=WHITE)
    # Líneas de contenido
    lx0 = fx + fw*0.15
    lx1 = fx + fw*0.85
    for i, ly in enumerate([0.42, 0.55, 0.68]):
        alpha = 180 if i == 0 else 120
        draw.line([lx0, fy + fh*ly, lx1, fy + fh*ly],
                  fill=(255, 255, 255, alpha), width=max(1, int(s*0.018)))

    # ── Texto "ATS" abajo ──
    text = "ATS"
    font_size = int(s * 0.16)
    try:
        font = ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except Exception:
        try:
            font = ImageFont.truetype(
                '/usr/share/fonts/liberation/LiberationSans-Bold.ttf', font_size)
        except Exception:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (s - tw) / 2 - bbox[0]
    ty = s * 0.75
    draw.text((tx, ty), text, fill=WHITE, font=font)

    # ── Subrayado decorativo bajo "ATS" ──
    ux = s*0.5 - tw*0.4
    uy = ty + (bbox[3] - bbox[1]) + s*0.01
    draw.rounded_rectangle([ux, uy, s*0.5 + tw*0.4, uy + max(2, int(s*0.012))],
                            radius=2, fill=(255, 255, 255, 160))

    return img


for size in SIZES:
    icon = generate_icon(size)
    path = os.path.join(OUTPUT_DIR, f'icon-{size}.png')
    icon.save(path, 'PNG')
    print(f'✓ icon-{size}.png')

print('\n¡Íconos generados exitosamente en static/img/')
