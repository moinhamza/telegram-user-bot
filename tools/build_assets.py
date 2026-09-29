#!/usr/bin/env python3
"""Build the Orbit background artwork assets:

  * assets/video/sky.mp4  1664x1248, 9 s, silent, seamless loop (slow push-in,
                          drifting moons, twinkling stars)
  * assets/images/sky.webp 1536x1024 still of the same artwork (poster/fallback)

The source is assets/images/sky-src.png, a painterly illustration whose pure
black sky band is cut off so the artwork line sits at y=499 of the 1248px frame
(i.e. right below the hero copy at 1563x1006).
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = "/home/user/telegram-user-bot"
SRC = f"{ROOT}/assets/images/sky-src.png"
OUT_VIDEO = f"{ROOT}/assets/video/sky.mp4"
OUT_STILL = f"{ROOT}/assets/images/sky.webp"
FFMPEG = "ffmpeg"  # any ffmpeg build with libx264 (piped rawvideo in, h264 out)

W, H = 1664, 1248          # video frame, per spec
FPS = 25
DUR = 9.0                  # seconds
NFRAMES = int(FPS * DUR)   # 225
HORIZON = 499              # illustration line: black band is the top 40%
CROP_TOP = 150             # rows of the source kept (keeps the flame tips)
FADE = 205                 # rows of sky above the artwork line melted into black

# --------------------------------------------------------------- source art
src = Image.open(SRC).convert("RGB")
art = src.crop((0, CROP_TOP, src.width, src.height))
aw, ah = art.size                      # 1264 x 698
# source row 296 (the artwork line) -> row 146 inside the crop
LINE_IN_CROP = 296 - CROP_TOP

# --- flatten the illustration's own horizontal sky bands (they leave seams) ---
def equalize_bands(img):
    """Smooth the row-wise background level so no band steps remain."""
    arr = np.asarray(img, dtype=np.float32)
    lum = arr.mean(axis=2)
    bg = np.percentile(lum, 5, axis=1)
    # wide moving average == step removal
    r = 40
    pad = np.pad(bg, r, mode="edge")
    ker = np.ones(2 * r + 1, dtype=np.float32) / (2 * r + 1)
    smooth = np.convolve(pad, ker, mode="valid")
    delta = smooth - bg
    weight = np.clip(1.0 - lum / 110.0, 0.0, 1.0)
    return np.clip(arr + delta[:, None, None] * weight[..., None], 0, 255)


art = Image.fromarray(equalize_bands(art).astype(np.uint8))

rng = np.random.default_rng(20260929)

# ------------------------------------------------------------------- stars
stars = []
for _ in range(250):
    stars.append((
        rng.uniform(4, W - 4),                 # x
        rng.uniform(6, 474),                   # y (black band + a little below)
        float(rng.choice([1.0, 1.0, 1.3, 1.6, 2.0, 2.5])),   # radius
        float(rng.uniform(0.35, 1.0)),         # base brightness
        float(rng.choice([1.5, 1.8, 2.0, 2.25, 3.0])),       # period (divides 9s)
        float(rng.uniform(0, 2 * math.pi)),    # phase
        float(rng.uniform(0.25, 0.65)),        # twinkle depth
    ))
flares = [(float(rng.uniform(60, W - 60)), float(rng.uniform(30, 430))) for _ in range(4)]


def blob(radius, size=None):
    """Small soft additive sprite (float, peak 1)."""
    if size is None:
        size = max(3, int(math.ceil(radius * 6)) | 1)
    yy, xx = np.mgrid[0:size, 0:size]
    c = (size - 1) / 2
    d2 = (xx - c) ** 2 + (yy - c) ** 2
    return np.exp(-d2 / (2 * max(radius, 0.35) ** 2))


def flare_sprite(radius=2.0, length=11.0, size=41):
    """Star with a small cross flare."""
    yy, xx = np.mgrid[0:size, 0:size]
    c = (size - 1) / 2
    g = np.exp(-(((xx - c) ** 2 + (yy - c) ** 2)) / (2 * radius ** 2))
    hx = np.exp(-((yy - c) ** 2) / (2 * 0.5 ** 2)) * np.exp(-np.abs(xx - c) / (length * 0.35))
    hy = np.exp(-((xx - c) ** 2) / (2 * 0.5 ** 2)) * np.exp(-np.abs(yy - c) / (length * 0.35))
    return np.clip(g + 0.45 * (hx + hy), 0, 1.4)


def moon_sprite(size=72, seed=3):
    """Grey moon sprite with soft shading, returns float RGB."""
    yy, xx = np.mgrid[0:size, 0:size]
    c = (size - 1) / 2
    r = size * 0.36
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    alpha = np.clip((r - d) / 1.4, 0, 1)
    nx, ny = (xx - c) / r, (yy - c) / r
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
    lam = np.clip(0.42 - 0.55 * nx - 0.45 * ny + 0.85 * nz, 0, 1)
    shade = 0.30 + 0.70 * lam
    noise = Image.fromarray((np.clip(shade, 0, 1) * 255).astype(np.uint8))
    noise = noise.filter(ImageFilter.GaussianBlur(2.2))
    shade = np.asarray(noise, dtype=np.float32) / 255.0
    noise = np.asarray(Image.fromarray(
        np.clip(0.5 + 0.5 * rng.normal(size=(size, size)) * 0.16, 0, 1,
                ).__mul__(255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)),
        dtype=np.float32) / 255.0
    tex = 0.80 + 0.40 * noise
    val = np.clip(shade * tex, 0, 1) * alpha * 0.72
    tint = np.array([0.82, 0.81, 0.88], dtype=np.float32)
    return val[..., None] * tint


moon_sprites = {26: moon_sprite(26, seed=3), 34: moon_sprite(34, seed=5),
                18: moon_sprite(18, seed=6)}
moons = [
    # (sprite size, anchor x, anchor y, drift x, drift y, period, phase)
    (34, W * 0.17, 150.0, 26.0, 9.0, 9.0, 0.0),
    (26, W * 0.80, 300.0, -22.0, 11.0, 9.0, 2.1),
    (18, W * 0.55, 88.0, 18.0, 6.0, 9.0, 4.3),
]


def stamp(buf, cx, cy, sprite, gain=1.0):
    """Additively stamp a 2-D sprite (h, w) onto buf (H, W, 3)."""
    h, w = sprite.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    ww = min(w - sx0, W - dx0)
    hh = min(h - sy0, H - dy0)
    if ww <= 0 or hh <= 0:
        return
    buf[dy0:dy0 + hh, dx0:dx0 + ww] += sprite[sy0:sy0 + hh, sx0:sx0 + ww] * gain


def colorize(gray, rgb):
    return gray[..., None] * np.asarray(rgb, dtype=np.float32)


# pre-render star sprites (additive, white with a cool tint)
RADII = (1.0, 1.3, 1.6, 2.0, 2.5)
AMPS = (0.45, 0.55, 0.70, 0.85, 1.0)
star_sprites = [colorize(blob(r, size=max(9, int(math.ceil(r * 8)) | 1)),
                         (0.94, 0.96, 1.0)) for r in RADII]
star_lookup = {r: i for i, r in enumerate(RADII)}
flare = colorize(flare_sprite(), (0.96, 0.97, 1.0))

# ------------------------------------------------------------------ frames
def render(idx):
    t = idx / FPS
    ph = 2 * math.pi * t / DUR

    # slow, loop-safe push-in on the illustration (horizon stays put)
    width = int(round(W * (1.0 + 0.013 * (1 - math.cos(ph)) / 2)))
    scale = width / aw
    height = int(round(ah * scale))
    layer = np.asarray(
        art.resize((width, height), Image.LANCZOS), dtype=np.float32) / 255.0
    # no hard seam: the artwork's own black band stays black, and its sky
    # level ramps gently back to the pure-black band above
    fade = min(height, int(round(FADE * scale)))
    if fade > 1:
        ramp = np.clip(np.arange(fade, dtype=np.float32) / (fade - 1), 0, 1) ** 1.6
        layer[:fade] *= ramp[:, None, None]
    canvas = np.zeros((H, W, 3), dtype=np.float32)
    x0 = (W - width) // 2
    y0 = int(round(HORIZON - LINE_IN_CROP * scale))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    ww = min(width - sx0, W - dx0)
    hh = min(height - sy0, H - dy0)
    canvas[dy0:dy0 + hh, dx0:dx0 + ww] = layer[sy0:sy0 + hh, sx0:sx0 + ww]

    # drifting moons (elliptical paths, period == clip length -> seamless)
    for radius, ax, ay, dx, dy, period, phase in moons:
        a = 2 * math.pi * (t / period) + phase
        stamp(canvas, ax + dx * math.sin(a), ay + dy * math.cos(a),
              moon_sprites[radius], 1.0)

    # twinkling stars
    for x, y, r, base, period, phase, amp in stars:
        k = 1.0 + amp * math.sin(2 * math.pi * t / period + phase)
        if k <= 0.02:
            continue
        sprite = star_sprites[star_lookup[r]]
        stamp(canvas, x, y, sprite, base * k * AMPS[star_lookup[r]] * 1.5)
    for i, (x, y) in enumerate(flares):
        k = 0.75 + 0.25 * math.sin(2 * math.pi * t / 3.0 + i * 1.7)
        stamp(canvas, x, y, flare, 0.9 * k)

    return np.clip(canvas * 255.0, 0, 255).astype(np.uint8)


proc = subprocess.Popen(
    [FFMPEG, "-y", "-loglevel", "error",
     "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
     "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
     "-pix_fmt", "yuv420p", "-g", str(FPS * 9), "-movflags", "+faststart",
     OUT_VIDEO],
    stdin=subprocess.PIPE)

for i in range(NFRAMES):
    proc.stdin.write(render(i).tobytes())
    if i % 25 == 0:
        print(f"frame {i}/{NFRAMES}", file=sys.stderr)
proc.stdin.close()
if proc.wait() != 0:
    raise SystemExit("ffmpeg failed")

# -------------------------------------------------------------------- still
frame = Image.fromarray(render(0))
still = frame.resize((1536, 1152), Image.LANCZOS).crop((0, 0, 1536, 1024))
still.save(OUT_STILL, "WEBP", quality=90, method=6)
print("wrote", OUT_VIDEO, "and", OUT_STILL, file=sys.stderr)
