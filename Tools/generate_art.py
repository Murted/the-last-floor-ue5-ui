import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

random.seed(7)
np.random.seed(7)

# ── Настройка ────────────────────────────────────────────────────────────
# По умолчанию — ровно тот путь, что указан в ArtPrompt.md. Переопределяется
# переменной окружения ART_OUTPUT_DIR (используется только для тестового
# прогона в песочнице, интерактивного ввода тут нет).
BASE_DIR = os.environ.get("ART_OUTPUT_DIR", r"D:\EpicGames\UnrealProjects\TheLastFloor")

# Единственное место, которое нужно менять, чтобы перегенерировать набор
# в другой палитре.
PALETTE = {
    "bg_darkest":   (0x05, 0x06, 0x0A),
    "panel":        (0x12, 0x15, 0x1E),
    "panel_border": (0x2A, 0x30, 0x40),
    "accent":       (0xE8, 0xA3, 0x3D),
    "health":       (0xC8, 0x41, 0x3B),
    "energy":       (0x3D, 0x9B, 0xE8),
    "currency":     (0xE8, 0xC2, 0x3D),
    "text_main":    (0xE6, 0xE8, 0xEC),
    "text_muted":   (0x8A, 0x90, 0xA0),
}

written = []


def save(img, relpath):
    full = os.path.join(BASE_DIR, relpath.replace("\\", os.sep))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    img.save(full, "PNG")
    written.append(full)


def lighten(rgb, amt):
    return tuple(min(255, int(c + (255 - c) * amt)) for c in rgb)


def darken(rgb, amt):
    return tuple(max(0, int(c * (1 - amt))) for c in rgb)


def desaturate(rgb):
    g = int(sum(rgb) / 3)
    return (g, g, g)


# ── Общие примитивы ─────────────────────────────────────────────────────

def vgradient(w, h, top_rgb, bottom_rgb):
    top = np.array(top_rgb, dtype=np.float32)
    bottom = np.array(bottom_rgb, dtype=np.float32)
    t = np.linspace(0, 1, h).reshape(h, 1, 1)
    grad = (top * (1 - t) + bottom * t).astype(np.uint8)
    grad_img = np.repeat(grad, w, axis=1)
    alpha = np.full((h, w, 1), 255, dtype=np.uint8)
    arr = np.concatenate([grad_img, alpha], axis=2)
    return Image.fromarray(arr, "RGBA")


def rounded_mask(w, h, radius):
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    return mask


def panel_like(w, h, radius, top_fill, bottom_fill, border_rgba, border_w=2):
    grad = vgradient(w, h, top_fill, bottom_fill)
    mask = rounded_mask(w, h, radius)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([border_w / 2, border_w / 2, w - 1 - border_w / 2, h - 1 - border_w / 2],
                         radius=radius, outline=border_rgba, width=border_w)
    return img


def radial_alpha(w, h, cx, cy, r, color, peak_alpha):
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    alpha = np.clip(1 - d, 0, 1) ** 1.6 * peak_alpha
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 0] = color[0]; arr[..., 1] = color[1]; arr[..., 2] = color[2]
    arr[..., 3] = alpha.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def edge_vignette(w, h, strength):
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    maxd = math.hypot(cx, cy)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / maxd
    alpha = (np.clip((d - 0.32) / 0.68, 0, 1) ** 1.4 * strength).astype(np.uint8)
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    black.putalpha(Image.fromarray(alpha, "L"))
    return black


def center_vignette(w, h, strength):
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    maxd = math.hypot(cx, cy)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / maxd
    alpha = (np.clip(1 - d / 0.85, 0, 1) ** 1.3 * strength).astype(np.uint8)
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    black.putalpha(Image.fromarray(alpha, "L"))
    return black


# ── Фоны ─────────────────────────────────────────────────────────────────

def tower_shaft(w, h, vp, n_rings, ring_base_alpha):
    img = Image.new("RGBA", (w, h), (*PALETTE["bg_darkest"], 255))
    draw = ImageDraw.Draw(img, "RGBA")
    vx, vy = vp
    max_extent = max(w, h) * 1.15
    for i in range(n_rings, 0, -1):
        t = i / n_rings
        scale = t ** 1.7
        rw = max_extent * scale
        rh = rw * 0.62
        x0, y0 = vx - rw / 2, vy - rh / 2
        x1, y1 = vx + rw / 2, vy + rh / 2
        a = int(ring_base_alpha * (0.3 + 0.7 * (1 - t)))
        col = (*lighten(PALETTE["bg_darkest"], 0.35), a)
        draw.rectangle([x0, y0, x1, y1], outline=col, width=2)
    return img


def bg_menu(w=1920, h=1080):
    img = tower_shaft(w, h, vp=(w * 0.5, h * 0.10), n_rings=11, ring_base_alpha=90)
    glow = radial_alpha(w, h, w * 0.5, h * 0.95, r=h * 0.75, color=PALETTE["accent"], peak_alpha=95)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, edge_vignette(w, h, strength=190))
    return img


def bg_results(w=1920, h=1080):
    img = tower_shaft(w, h, vp=(w * 0.5, h * 0.08), n_rings=9, ring_base_alpha=70)
    glow = radial_alpha(w, h, w * 0.5, h * 0.05, r=h * 0.6, color=PALETTE["energy"], peak_alpha=80)
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, center_vignette(w, h, strength=150))
    return img


def bg_noise(size=512, alpha_pct=0.04):
    noise = np.random.rand(size, size).astype(np.float32)
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = 210; arr[..., 1] = 212; arr[..., 2] = 218
    arr[..., 3] = (noise * 255 * alpha_pct).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ── UI-элементы ──────────────────────────────────────────────────────────

def make_panel():
    top = lighten(PALETTE["panel"], 0.04)
    return panel_like(128, 128, 12, top, PALETTE["panel"], (*PALETTE["panel_border"], 255), border_w=2)


def make_tooltip():
    fill = darken(PALETTE["panel"], 0.3)
    top = lighten(fill, 0.05)
    return panel_like(128, 128, 10, top, fill, (*PALETTE["accent"], 102), border_w=2)


def make_button(state):
    p = PALETTE["panel"]
    if state == "normal":
        top, bottom, border = lighten(p, 0.06), p, (*PALETTE["panel_border"], 255)
    elif state == "hovered":
        top, bottom, border = lighten(p, 0.18), lighten(p, 0.06), (*PALETTE["accent"], 255)
    elif state == "pressed":
        top, bottom, border = darken(p, 0.25), lighten(p, 0.10), (*lighten(PALETTE["accent"], 0.15), 255)
    img = panel_like(128, 64, 10, top, bottom, border, border_w=2)
    return img


def make_button_disabled():
    base = make_button("normal")
    gray = ImageOps.grayscale(base.convert("RGB")).convert("RGB")
    gray_rgba = Image.merge("RGBA", (*gray.split(), base.split()[3]))
    alpha = gray_rgba.split()[3].point(lambda a: int(a * 0.45))
    gray_rgba.putalpha(alpha)
    return gray_rgba


def make_bar_bg():
    top = darken(PALETTE["bg_darkest"], -0.0)
    img = panel_like(256, 32, 6, PALETTE["bg_darkest"], lighten(PALETTE["bg_darkest"], 0.03),
                      (*PALETTE["panel_border"], 220), border_w=1)
    # лёгкая внутренняя тень сверху
    shade = vgradient(256, 10, (0, 0, 0), (0, 0, 0))
    shade.putalpha(Image.new("L", (256, 10), 90))
    mask = rounded_mask(256, 32, 6).crop((0, 0, 256, 10))
    img.paste(Image.alpha_composite(img.crop((0, 0, 256, 10)), shade), (0, 0), mask)
    return img


def make_bar_fill():
    img = panel_like(256, 32, 6, (255, 255, 255), (222, 222, 226), (0, 0, 0, 0), border_w=0)
    highlight = Image.new("RGBA", (256, 32), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.rounded_rectangle([2, 2, 254, 12], radius=5, fill=(255, 255, 255, 110))
    img = Image.alpha_composite(img, highlight)
    return img


def make_banner_threat(w=512, h=128):
    xx = np.tile(np.linspace(-1, 1, w), (h, 1))
    yy = np.tile(np.linspace(-1, 1, h).reshape(h, 1), (1, w))
    fx = np.clip(1 - np.abs(xx) ** 1.4, 0, 1)
    fy = np.clip(1 - np.abs(yy) ** 1.8, 0, 1)
    a = (fx * fy * 235).astype(np.uint8)
    col = lighten(PALETTE["health"], 0.05)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 0] = col[0]; arr[..., 1] = col[1]; arr[..., 2] = col[2]
    arr[..., 3] = a
    img = Image.fromarray(arr, "RGBA")
    edge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge)
    ed.rectangle([0, 8, w - 1, 9], fill=(*lighten(PALETTE["health"], 0.4), 160))
    ed.rectangle([0, h - 10, w - 1, h - 9], fill=(*lighten(PALETTE["health"], 0.4), 160))
    mask = Image.fromarray(a, "L")
    edge.putalpha(ImageOps.autocontrast(mask).point(lambda v: min(v, 160)))
    return img


def make_slot(highlight=False):
    fill = lighten(PALETTE["panel"], 0.08)
    top = lighten(fill, 0.04)
    border = (*PALETTE["accent"], 255) if highlight else (*PALETTE["panel_border"], 255)
    bw = 3 if highlight else 2
    return panel_like(96, 96, 8, top, fill, border, border_w=bw)


# ── Иконки: геометрический помощник ────────────────────────────────────

def P(x0, y0, x1, y1, nx, ny):
    return (x0 + (x1 - x0) * nx, y0 + (y1 - y0) * ny)


def draw_icon(draw, bbox, name, color):
    x0, y0, x1, y1 = bbox
    def p(nx, ny):
        return P(x0, y0, x1, y1, nx, ny)
    w = x1 - x0

    if name == "heart":
        r = w * 0.26
        draw.ellipse([*p(0.12, 0.10), *p(0.52, 0.50)], fill=color)
        draw.ellipse([*p(0.48, 0.10), *p(0.88, 0.50)], fill=color)
        draw.polygon([p(0.08, 0.38), p(0.92, 0.38), p(0.5, 0.95)], fill=color)
    elif name == "lightning":
        draw.polygon([p(0.58, 0.02), p(0.18, 0.58), p(0.46, 0.58), p(0.32, 0.98),
                      p(0.82, 0.40), p(0.52, 0.40)], fill=color)
    elif name == "coin":
        draw.ellipse([*p(0.08, 0.08), *p(0.92, 0.92)], fill=color)
        draw.ellipse([*p(0.30, 0.30), *p(0.70, 0.70)], fill=(0, 0, 0, 0))
        _punch_ellipse(draw, p(0.30, 0.30), p(0.70, 0.70))
    elif name == "stairs":
        steps = 4
        sw, sh = 1.0 / steps, 1.0 / steps
        for i in range(steps):
            draw.rectangle([*p(i * sw, 1 - (i + 1) * sh), *p(1.0, 1.0)], fill=color)
    elif name == "skull":
        draw.ellipse([*p(0.15, 0.05), *p(0.85, 0.65)], fill=color)
        draw.rectangle([*p(0.30, 0.55), *p(0.70, 0.85)], fill=color)
        _punch_ellipse(draw, p(0.26, 0.28), p(0.46, 0.48))
        _punch_ellipse(draw, p(0.54, 0.28), p(0.74, 0.48))
    elif name == "shield":
        draw.polygon([p(0.5, 0.02), p(0.92, 0.18), p(0.92, 0.55), p(0.5, 0.98),
                      p(0.08, 0.55), p(0.08, 0.18)], fill=color)
    elif name == "sword":
        draw.rectangle([*p(0.46, 0.02), *p(0.54, 0.66)], fill=color)
        draw.rectangle([*p(0.24, 0.62), *p(0.76, 0.72)], fill=color)
        draw.rectangle([*p(0.42, 0.72), *p(0.58, 0.96)], fill=color)
    elif name == "hourglass":
        draw.polygon([p(0.12, 0.05), p(0.88, 0.05), p(0.5, 0.48)], fill=color)
        draw.polygon([p(0.12, 0.95), p(0.88, 0.95), p(0.5, 0.52)], fill=color)
    elif name == "gear":
        cx, cy = p(0.5, 0.5)
        r_out, r_in = w * 0.36, w * 0.22
        teeth = 8
        pts = []
        for i in range(teeth * 2):
            ang = math.pi * 2 * i / (teeth * 2)
            r = r_out if i % 2 == 0 else r_out * 0.78
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        draw.polygon(pts, fill=color)
        draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=(0, 0, 0, 0))
        _punch_ellipse(draw, (cx - r_in, cy - r_in), (cx + r_in, cy + r_in))
    elif name == "close":
        draw.line([p(0.12, 0.12), p(0.88, 0.88)], fill=color, width=int(w * 0.14))
        draw.line([p(0.88, 0.12), p(0.12, 0.88)], fill=color, width=int(w * 0.14))
    elif name == "arrow_left":
        draw.polygon([p(0.65, 0.08), p(0.65, 0.92), p(0.15, 0.5)], fill=color)
    elif name == "arrow_right":
        draw.polygon([p(0.35, 0.08), p(0.35, 0.92), p(0.85, 0.5)], fill=color)
    elif name == "plus":
        draw.rectangle([*p(0.40, 0.08), *p(0.60, 0.92)], fill=color)
        draw.rectangle([*p(0.08, 0.40), *p(0.92, 0.60)], fill=color)
    elif name == "lock":
        draw.rounded_rectangle([*p(0.18, 0.42), *p(0.82, 0.92)], radius=int(w * 0.06), fill=color)
        draw.arc([*p(0.28, 0.05), *p(0.72, 0.62)], start=180, end=360, fill=color, width=int(w * 0.1))
    elif name == "eye":
        draw.ellipse([*p(0.05, 0.30), *p(0.95, 0.70)], fill=color)
        _punch_ellipse(draw, p(0.40, 0.36), p(0.60, 0.64))
    elif name == "question":
        draw.arc([*p(0.22, 0.05), *p(0.78, 0.60)], start=200, end=470, fill=color, width=int(w * 0.14))
        draw.line([p(0.5, 0.55), p(0.5, 0.72)], fill=color, width=int(w * 0.14))
        draw.ellipse([*p(0.42, 0.82), *p(0.58, 0.98)], fill=color)


def _punch_ellipse(draw, xy0, xy1):
    draw.ellipse([*xy0, *xy1], fill=(0, 0, 0, 0))


RELIC_SHAPES = ["crystal", "ring", "vial", "feather", "bone", "flame", "eye", "key",
                "compass", "mask", "gear", "scroll", "thorn", "star", "hourglass", "shard"]


def draw_relic(draw, bbox, name):
    x0, y0, x1, y1 = bbox
    def p(nx, ny):
        return P(x0, y0, x1, y1, nx, ny)
    w = x1 - x0
    outline = (*darken(PALETTE["bg_darkest"], -0.0), 255)

    def poly(pts, color):
        draw.polygon(pts, fill=(*color, 255))
        draw.line(pts + [pts[0]], fill=(0, 0, 0, 110), width=max(2, int(w * 0.012)))

    if name == "crystal":
        poly([p(0.5, 0.04), p(0.82, 0.36), p(0.66, 0.96), p(0.34, 0.96), p(0.18, 0.36)], PALETTE["energy"])
    elif name == "ring":
        c = PALETTE["currency"]
        draw.ellipse([*p(0.20, 0.36), *p(0.80, 0.96)], fill=(*c, 255))
        _punch_ellipse(draw, p(0.34, 0.50), p(0.66, 0.82))
        draw.polygon([p(0.50, 0.04), p(0.66, 0.30), p(0.34, 0.30)], fill=(*lighten(c, 0.2), 255))
    elif name == "vial":
        c = PALETTE["energy"]
        draw.rectangle([*p(0.42, 0.04), *p(0.58, 0.22)], fill=(*c, 255))
        draw.polygon([p(0.30, 0.22), p(0.70, 0.22), p(0.82, 0.70), p(0.66, 0.96),
                      p(0.34, 0.96), p(0.18, 0.70)], fill=(*c, 255))
    elif name == "feather":
        c = PALETTE["text_main"]
        draw.polygon([p(0.5, 0.02), p(0.85, 0.5), p(0.5, 0.98), p(0.5, 0.02)], fill=(*c, 255))
        draw.line([p(0.5, 0.05), p(0.5, 0.95)], fill=(*PALETTE["panel_border"], 255), width=max(2, int(w * 0.02)))
    elif name == "bone":
        c = PALETTE["text_muted"]
        draw.rounded_rectangle([*p(0.30, 0.42), *p(0.70, 0.58)], radius=int(w * 0.08), fill=(*c, 255))
        for cx, cy in [(0.22, 0.28), (0.22, 0.72), (0.78, 0.28), (0.78, 0.72)]:
            r = w * 0.11
            ax, ay = p(cx, cy)
            draw.ellipse([ax - r, ay - r, ax + r, ay + r], fill=(*c, 255))
    elif name == "flame":
        c = PALETTE["accent"]
        draw.polygon([p(0.5, 0.02), p(0.78, 0.42), p(0.66, 0.42), p(0.86, 0.98),
                      p(0.14, 0.98), p(0.34, 0.55), p(0.22, 0.55)], fill=(*c, 255))
        draw.polygon([p(0.5, 0.30), p(0.62, 0.55), p(0.5, 0.98), p(0.38, 0.55)], fill=(*lighten(c, 0.4), 255))
    elif name == "eye":
        c = PALETTE["energy"]
        draw.ellipse([*p(0.05, 0.32), *p(0.95, 0.68)], fill=(*c, 255))
        draw.ellipse([*p(0.38, 0.34), *p(0.62, 0.66)], fill=(*darken(PALETTE["bg_darkest"], -0.0), 255))
    elif name == "key":
        c = PALETTE["currency"]
        draw.ellipse([*p(0.10, 0.10), *p(0.50, 0.50)], fill=(*c, 255))
        _punch_ellipse(draw, p(0.22, 0.22), p(0.38, 0.38))
        draw.rectangle([*p(0.44, 0.24), *p(0.90, 0.36)], fill=(*c, 255))
        draw.rectangle([*p(0.70, 0.36), *p(0.80, 0.48)], fill=(*c, 255))
        draw.rectangle([*p(0.82, 0.36), *p(0.90, 0.52)], fill=(*c, 255))
    elif name == "compass":
        c = PALETTE["accent"]
        draw.ellipse([*p(0.08, 0.08), *p(0.92, 0.92)], outline=(*c, 255), width=max(3, int(w * 0.035)))
        draw.polygon([p(0.5, 0.15), p(0.58, 0.5), p(0.5, 0.85), p(0.42, 0.5)], fill=(*lighten(c, 0.2), 255))
    elif name == "mask":
        c = PALETTE["text_muted"]
        draw.ellipse([*p(0.10, 0.10), *p(0.90, 0.90)], fill=(*c, 255))
        _punch_ellipse(draw, p(0.24, 0.36), p(0.42, 0.52))
        _punch_ellipse(draw, p(0.58, 0.36), p(0.76, 0.52))
        draw.polygon([p(0.30, 0.68), p(0.70, 0.68), p(0.5, 0.82)], fill=(0, 0, 0, 0))
    elif name == "gear":
        draw_icon(draw, bbox, "gear", (*PALETTE["text_muted"], 255))
    elif name == "scroll":
        c = PALETTE["text_main"]
        draw.rounded_rectangle([*p(0.20, 0.12), *p(0.80, 0.88)], radius=int(w * 0.10), fill=(*c, 255))
        for f in (0.30, 0.45, 0.60, 0.75):
            draw.line([p(0.30, f), p(0.70, f)], fill=(*PALETTE["panel_border"], 255), width=max(2, int(w * 0.015)))
    elif name == "thorn":
        c = PALETTE["health"]
        draw.polygon([p(0.5, 0.02), p(0.62, 0.5), p(0.5, 0.98), p(0.38, 0.5)], fill=(*c, 255))
        draw.polygon([p(0.5, 0.30), p(0.85, 0.42), p(0.5, 0.5)], fill=(*c, 255))
        draw.polygon([p(0.5, 0.30), p(0.15, 0.42), p(0.5, 0.5)], fill=(*c, 255))
    elif name == "star":
        c = PALETTE["currency"]
        cx, cy = p(0.5, 0.5)
        r_out, r_in = w * 0.46, w * 0.19
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + math.pi * i / 5
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        draw.polygon(pts, fill=(*c, 255))
    elif name == "hourglass":
        c = PALETTE["energy"]
        draw.polygon([p(0.15, 0.06), p(0.85, 0.06), p(0.5, 0.48)], fill=(*c, 255))
        draw.polygon([p(0.15, 0.94), p(0.85, 0.94), p(0.5, 0.52)], fill=(*c, 255))
    elif name == "shard":
        c = PALETTE["energy"]
        draw.polygon([p(0.5, 0.02), p(0.9, 0.4), p(0.7, 0.98), p(0.3, 0.98), p(0.1, 0.4)], fill=(*c, 255))
        draw.polygon([p(0.5, 0.02), p(0.9, 0.4), p(0.5, 0.55)], fill=(*lighten(c, 0.35), 255))


UI_ICONS = ["heart", "lightning", "coin", "stairs", "skull", "shield", "sword", "hourglass",
            "gear", "close", "arrow_left", "arrow_right", "plus", "lock", "eye", "question"]


def make_icon_atlas_ui(cell=64, cols=4, rows=4, pad_pct=0.12):
    size = cell * cols
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    cells = {}
    for i, name in enumerate(UI_ICONS):
        r, c = divmod(i, cols)
        x0, y0 = c * cell, r * cell
        pad = cell * pad_pct
        bbox = (x0 + pad, y0 + pad, x0 + cell - pad, y0 + cell - pad)
        draw_icon(draw, bbox, name, (255, 255, 255, 255))
        cells[name] = (x0, y0, cell, cell)
    return img, cells


def make_icon_atlas_relics(cell=128, cols=4, rows=4, pad_pct=0.12):
    size = cell * cols
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    cells = {}
    for i, name in enumerate(RELIC_SHAPES):
        r, c = divmod(i, cols)
        x0, y0 = c * cell, r * cell
        pad = cell * pad_pct
        bbox = (x0 + pad, y0 + pad, x0 + cell - pad, y0 + cell - pad)
        draw_relic(draw, bbox, name)
        cells[name] = (x0, y0, cell, cell)
    return img, cells


# ── Генерация ────────────────────────────────────────────────────────────

save(bg_menu(), "Content/Textures/Backgrounds/T_BG_Menu.png")
save(bg_results(), "Content/Textures/Backgrounds/T_BG_Results.png")
save(bg_noise(), "Content/Textures/Backgrounds/T_BG_Noise.png")

save(make_panel(), "Content/Textures/UI/T_Panel_9S.png")
save(make_tooltip(), "Content/Textures/UI/T_Tooltip_9S.png")
save(make_button("normal"), "Content/Textures/UI/T_Button_Normal_9S.png")
save(make_button("hovered"), "Content/Textures/UI/T_Button_Hovered_9S.png")
save(make_button("pressed"), "Content/Textures/UI/T_Button_Pressed_9S.png")
save(make_button_disabled(), "Content/Textures/UI/T_Button_Disabled_9S.png")
save(make_bar_bg(), "Content/Textures/UI/T_Bar_BG.png")
save(make_bar_fill(), "Content/Textures/UI/T_Bar_Fill.png")
save(make_banner_threat(), "Content/Textures/UI/T_Banner_Threat.png")
save(make_slot(False), "Content/Textures/UI/T_Slot_9S.png")
save(make_slot(True), "Content/Textures/UI/T_Slot_Highlight_9S.png")

ui_atlas, ui_cells = make_icon_atlas_ui()
save(ui_atlas, "Content/Textures/Atlases/T_Icons_UI.png")

relic_atlas, relic_cells = make_icon_atlas_relics()
save(relic_atlas, "Content/Textures/Atlases/T_Icons_Relics.png")

# ── Манифест ─────────────────────────────────────────────────────────────

RU_NAMES_UI = {
    "heart": "сердце", "lightning": "молния", "coin": "монета", "stairs": "лестница",
    "skull": "череп", "shield": "щит", "sword": "меч", "hourglass": "песочные часы",
    "gear": "шестерёнка", "close": "крест-закрыть", "arrow_left": "стрелка-влево",
    "arrow_right": "стрелка-вправо", "plus": "плюс", "lock": "замок", "eye": "глаз",
    "question": "вопрос",
}
RU_NAMES_RELICS = {
    "crystal": "кристалл", "ring": "кольцо", "vial": "фиал", "feather": "перо",
    "bone": "кость", "flame": "пламя", "eye": "око", "key": "ключ",
    "compass": "компас", "mask": "маска", "gear": "шестерня", "scroll": "свиток",
    "thorn": "шип", "star": "звезда", "hourglass": "песочные часы", "shard": "осколок",
}

lines = []
lines.append("# ArtManifest — THE LAST FLOOR\n")
lines.append("Сгенерировано скриптом `Tools/generate_art.py`. Все текстуры — PNG, RGBA, прямая альфа.\n")

lines.append("## Фоны — `Content/Textures/Backgrounds/`\n")
lines.append("| Файл | Размер | Назначение |")
lines.append("|---|---|---|")
lines.append("| T_BG_Menu.png | 1920×1080 | Фон главного меню |")
lines.append("| T_BG_Results.png | 1920×1080 | Фон экрана итогов |")
lines.append("| T_BG_Noise.png | 512×512 | Бесшовный шум, альфа ~4%, тайлится под панелями |\n")

lines.append("## UI — `Content/Textures/UI/`\n")
lines.append("| Файл | Размер | 9-slice поле | Назначение |")
lines.append("|---|---|---|---|")
lines.append("| T_Panel_9S.png | 128×128 | 24 px | Базовая панель |")
lines.append("| T_Tooltip_9S.png | 128×128 | 24 px | Тултип |")
lines.append("| T_Button_Normal_9S.png | 128×64 | 16 px | Кнопка, состояние Normal |")
lines.append("| T_Button_Hovered_9S.png | 128×64 | 16 px | Кнопка, состояние Hovered |")
lines.append("| T_Button_Pressed_9S.png | 128×64 | 16 px | Кнопка, состояние Pressed |")
lines.append("| T_Button_Disabled_9S.png | 128×64 | 16 px | Кнопка, состояние Disabled |")
lines.append("| T_Bar_BG.png | 256×32 | — | Подложка полосы (здоровье/энергия) |")
lines.append("| T_Bar_Fill.png | 256×32 | — | Заливка полосы, белая, тонируется в UMG |")
lines.append("| T_Banner_Threat.png | 512×128 | — | Баннер угрозы |")
lines.append("| T_Slot_9S.png | 96×96 | 16 px | Ячейка инвентаря |")
lines.append("| T_Slot_Highlight_9S.png | 96×96 | 16 px | Ячейка инвентаря, подсветка drag&drop |\n")

lines.append("## Атласы — `Content/Textures/Atlases/`\n")
lines.append("### T_Icons_UI.png — 256×256, сетка 4×4, ячейка 64×64, белые силуэты\n")
lines.append("| Индекс | Файл-идентификатор | Что изображено | x,y,w,h (px) |")
lines.append("|---|---|---|---|")
for i, name in enumerate(UI_ICONS):
    x, y, cw, ch = ui_cells[name]
    lines.append(f"| {i} | {name} | {RU_NAMES_UI[name]} | {x},{y},{cw},{ch} |")

lines.append("\n### T_Icons_Relics.png — 512×512, сетка 4×4, ячейка 128×128, цветные\n")
lines.append("| Индекс | Файл-идентификатор | Что изображено | x,y,w,h (px) |")
lines.append("|---|---|---|---|")
for i, name in enumerate(RELIC_SHAPES):
    x, y, cw, ch = relic_cells[name]
    lines.append(f"| {i} | {name} | {RU_NAMES_RELICS[name]} | {x},{y},{cw},{ch} |")

lines.append("\n## Настройки импорта в Unreal (одинаковые для всех файлов)\n")
lines.append("- Texture Group: **UI**")
lines.append("- Compression Settings: **UserInterface2D (RGBA)**")
lines.append("- Mip Gen Settings: **NoMipmaps**")
lines.append("- sRGB: **включён**\n")

manifest_path = os.path.join(BASE_DIR, "Docs", "ArtManifest.md")
os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
with open(manifest_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
written.append(manifest_path)

for p in written:
    print(p)
