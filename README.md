# Orbit — single-file landing page

`index.html` is the whole landing page: plain HTML, one inline `<style>`, inline
`<script>`s, no frameworks, no build step. It is a full-screen, non-scrolling
hero for the fictional space product "Orbit".

Open it directly (`index.html`) or serve the folder with any static server:

```
python3 -m http.server 8099
```

## Scaling

The composition was measured from a 1563×1006 reference render. One CSS
variable `--u` equals one reference pixel, and every size, offset, font size,
letter-spacing, radius, gap and border is written as `calc(N * var(--u))`, so
the whole layout scales as one rigid unit (see the `:root` block and the
responsive `@media` overrides at the bottom of the stylesheet).

## Assets

| File | What it is |
| --- | --- |
| `assets/fonts/inter-var.woff2` | Inter v4 variable (axes `opsz` 14–32, `wght` 100–900), self-hosted |
| `assets/video/sky.mp4` | Background artwork loop, 1664×1248, 9 s, silent (H.264, faststart) |
| `assets/images/sky.webp` | Poster / fallback still of the same artwork, 1536×1024 |
| `assets/images/sky-src.png` | Source illustration the two assets above are rendered from |
| `tools/build_assets.py` | Builds the video (push-in, drifting moons, twinkling stars) and the still from the source illustration |

The artwork is a painterly illustration: pure black upper half, a dark cratered
ringed planet in front of mint-green flame-shaped clouds, small moons and
asteroids, two satellites and large purple cumulus clouds across the bottom. In
the video the moons drift and the stars twinkle; the 9 s loop is seamless.

`tools/build_assets.py` needs Python with `numpy`/`Pillow` and an `ffmpeg` with
libx264 on `PATH`:

```
python3 tools/build_assets.py
```
