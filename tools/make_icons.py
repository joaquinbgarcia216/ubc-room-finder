"""Draws the extension icons (run from the repo root)."""
from PIL import Image, ImageDraw
S = 1024  # draw big, downsample for smooth edges
NAVY = (0, 33, 69, 255); WHITE = (255, 255, 255, 255); GREEN = (46, 160, 90, 255)

def icon(pad_frac):
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    p = int(S * pad_frac)
    d.rounded_rectangle([p, p, S - p, S - p], radius=int((S - 2 * p) * 0.22), fill=NAVY)
    # map pin: circle head + triangle tail
    cx, cy, r = S / 2, S * 0.43, (S - 2 * p) * 0.27
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.polygon([(cx - r * 0.82, cy + r * 0.55), (cx + r * 0.82, cy + r * 0.55), (cx, cy + r * 2.05)], fill=WHITE)
    # door inside pin head
    dw, dh = r * 0.62, r * 0.98
    d.rounded_rectangle([cx - dw / 2, cy - dh / 2, cx + dw / 2, cy + dh / 2], radius=int(r * 0.08), fill=NAVY)
    # door knob (green = free)
    k = r * 0.11
    d.ellipse([cx + dw * 0.22 - k, cy + dh * 0.05 - k, cx + dw * 0.22 + k, cy + dh * 0.05 + k], fill=GREEN)
    return im

# Store guidance: 128px icon with ~96px artwork and transparent padding
icon(16 / 128).resize((128, 128), Image.LANCZOS).save('extension/icons/icon128.png')
small = icon(0.04)
for n in (16, 32, 48):
    small.resize((n, n), Image.LANCZOS).save(f'extension/icons/icon{n}.png')
print('ok')
