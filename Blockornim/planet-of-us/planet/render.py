"""Renders one simulated day as a vertical Short: a lit, rotating 3D globe with clouds, night-side
city lights, atmosphere, meteor impacts, a HUD and procedural sound (720x1280, 30 fps, H.264 + AAC)."""
from __future__ import annotations

import copy
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import audio
from .noise import fractal
from .sim import POLAR_ROWS, SEA_LEVEL, TEX_SCALE, THREATS, DayResult, World

W, H = 720, 1280
FPS = 30
PLANET_R = 270
PLANET_C = (W // 2, 590)
TILT = math.radians(20)
SPIN = 0.22                     # radians per second
LIGHT = np.array([-0.62, -0.42, 0.66])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
ATMO = np.array([0.35, 0.62, 1.0], np.float32)

TEXT = (240, 243, 250)
MUTED = (160, 170, 190)
KIND_COLOR = {
    "nation": (70, 150, 255), "contact": (60, 200, 170), "monument": (240, 190, 70),
    "warning": (255, 90, 60), "hit": (255, 70, 50), "saved": (80, 220, 120), "death": (200, 40, 40),
    "quiet": (90, 100, 130),
}

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def _font(size: int, bold: bool = True):
    try:
        return ImageFont.truetype(str(FONT_DIR / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)
    except OSError:
        return ImageFont.load_default(size)


F_TITLE, F_DAY, F_BODY, F_SMALL, F_BANNER, F_LABEL = (
    _font(24), _font(78), _font(26, False), _font(19, False), _font(28), _font(20))


def _smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


@dataclass
class Snapshot:
    owner: list
    crater: list


def snapshot(world: World) -> Snapshot:
    return Snapshot(copy.deepcopy(world.owner), copy.deepcopy(world.crater))


class Globe:
    """Everything that stays fixed for a world: terrain texture, clouds, sphere geometry, background."""

    def __init__(self, world: World):
        self.world = world
        el = world.elevation
        self.th, self.tw = el.shape
        rng = np.random.default_rng(world.seed + 7)
        self.base, self.ocean = self._terrain(el, rng)
        cloud = fractal(self.th, self.tw, world.seed + 101, octaves=7, base=4)
        self.cloud = (np.clip((cloud - 0.5) / 0.28, 0, 1) ** 1.4 * 0.9).astype(np.float32)
        self.citydots = ((rng.random((self.th, self.tw)) < 0.07) * (0.4 + 0.6 * rng.random((self.th, self.tw))))
        self.citydots = self.citydots.astype(np.float32)
        self._geometry()
        self.bg = self._background(rng)

    # ---------- static layers ----------
    def _terrain(self, el: np.ndarray, rng) -> tuple[np.ndarray, np.ndarray]:
        detail = fractal(self.th, self.tw, self.world.seed + 55, octaves=7, base=16)
        tex = np.zeros((self.th, self.tw, 3), np.float32)
        ocean = el <= SEA_LEVEL
        depth = np.clip((SEA_LEVEL - el) / SEA_LEVEL, 0, 1)[..., None]
        deep, shallow = np.array([0.02, 0.10, 0.26]), np.array([0.06, 0.32, 0.50])
        tex = np.where(ocean[..., None], shallow * (1 - depth) ** 1.5 + deep * (1 - (1 - depth) ** 1.5), tex)
        hgt = np.clip((el - SEA_LEVEL) / (1 - SEA_LEVEL), 0, 1)[..., None]
        stops = [(0.00, (0.80, 0.74, 0.52)), (0.03, (0.20, 0.50, 0.16)), (0.22, (0.10, 0.36, 0.12)),
                 (0.45, (0.36, 0.42, 0.18)), (0.65, (0.46, 0.38, 0.28)), (0.82, (0.55, 0.52, 0.50)),
                 (0.93, (0.95, 0.96, 0.98)), (1.00, (0.98, 0.98, 1.0))]
        land = np.zeros_like(tex)
        for (h0, c0), (h1, c1) in zip(stops, stops[1:]):
            k = np.clip((hgt - h0) / (h1 - h0), 0, 1)
            seg = (hgt >= h0) & (hgt <= h1)
            land = np.where(seg, np.array(c0) * (1 - k) + np.array(c1) * k, land)
        land *= (0.85 + 0.3 * detail[..., None])
        tex = np.where(ocean[..., None], tex, land)
        # polar ice
        rows = np.arange(self.th)[:, None]
        polar = int(self.th * POLAR_ROWS)
        edge = polar + (detail - 0.5) * self.th * 0.06
        ice = (rows < edge) | (rows > self.th - 1 - edge)
        tex = np.where(ice[..., None], np.array([0.86, 0.91, 0.97]) * (0.9 + 0.1 * detail[..., None]), tex)
        return tex.astype(np.float32), (ocean & ~ice).astype(np.float32)

    def _geometry(self):
        R = PLANET_R
        ys, xs = np.mgrid[-R:R, -R:R] + 0.5
        nx, ny = xs / R, ys / R
        r2 = nx * nx + ny * ny
        self.mask = r2 <= 1.0
        nz = np.sqrt(np.clip(1 - r2, 0, 1))
        c, s = math.cos(TILT), math.sin(TILT)
        y2 = ny * c - nz * s
        z2 = ny * s + nz * c
        lat = np.arcsin(np.clip(-y2, -1, 1))
        self.lon0 = np.arctan2(nx, z2)
        self.v = np.clip(((0.5 - lat / math.pi) * self.th).astype(np.int32), 0, self.th - 1)
        ndotl = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
        self.light = np.clip(ndotl, 0, 1).astype(np.float32)[..., None]
        self.night = (1 - _smooth(-0.18, 0.15, ndotl)).astype(np.float32)[..., None]
        half = LIGHT + np.array([0, 0, 1.0])
        half /= np.linalg.norm(half)
        self.spec = (np.clip(nx * half[0] + ny * half[1] + nz * half[2], 0, 1) ** 70).astype(np.float32)[..., None]
        self.rim = ((1 - nz) ** 2.2).astype(np.float32)[..., None]
        self.rim_lit = (0.25 + 0.75 * _smooth(-0.4, 0.4, ndotl)).astype(np.float32)[..., None]

    def _background(self, rng) -> np.ndarray:
        bg = np.zeros((H, W, 3), np.float32)
        yy = np.linspace(0, 1, H)[:, None, None]
        bg += np.array([0.01, 0.015, 0.04]) * (1 - yy) + np.array([0.02, 0.01, 0.035]) * yy
        neb = fractal(H // 4, W // 4, self.world.seed + 9, octaves=5, base=3)
        neb = np.asarray(Image.fromarray((neb * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
        bg += (neb ** 3)[..., None] * np.array([0.10, 0.04, 0.16])
        n = 900
        sx, sy = rng.integers(0, W, n), rng.integers(0, H, n)
        b = rng.random(n) ** 3
        bg[sy, sx] += b[:, None] * np.array([0.9, 0.92, 1.0])
        big = rng.random(n) > 0.97
        for x, y in zip(sx[big], sy[big]):
            bg[max(0, y - 1):y + 2, max(0, x - 1):x + 2] += 0.25
        # outer atmosphere glow
        cx, cy = PLANET_C
        ys, xs = np.mgrid[0:H, 0:W]
        r = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / PLANET_R
        dirl = ((xs - cx) * LIGHT[0] + (ys - cy) * LIGHT[1]) / (r * PLANET_R + 1e-6)
        glow = np.exp(-np.clip(r - 1, 0, None) * 11) * (r > 0.98) * (0.35 + 0.65 * np.clip(dirl * 0.8 + 0.4, 0, 1))
        bg += glow[..., None] * ATMO * 0.55
        return np.clip(bg, 0, 1)

    # ---------- per-state surface ----------
    def surface(self, owner: np.ndarray, colors: np.ndarray, crater: np.ndarray, heat: np.ndarray,
                flash: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        s = TEX_SCALE

        def up(a):
            return np.repeat(np.repeat(a, s, axis=0), s, axis=1)

        def soft(a):
            # bilinear upsample so nation borders follow smooth curves instead of square tiles
            img = Image.fromarray(a.astype(np.float32), mode="F").resize((self.tw, self.th), Image.BILINEAR)
            return np.asarray(img, np.float32)

        own = owner >= 0
        tile_col = np.zeros(owner.shape + (3,), np.float32)
        if colors.size:
            tile_col[own] = colors[owner[own]]
        diff = np.zeros_like(own)
        for ax, sh in ((1, 1), (1, -1), (0, 1), (0, -1)):
            diff |= np.roll(owner, sh, axis=ax) != owner
        border = own & diff
        alpha = np.where(border, 0.9, np.where(own, 0.42, 0.0)).astype(np.float32)
        tex = self.base.copy()
        a = soft(alpha)[..., None]
        prem = np.stack([soft(tile_col[..., c] * alpha) for c in range(3)], axis=-1)
        tex = tex * (1 - a) + prem
        tex += soft(flash)[..., None] * 0.7
        # craters: glowing when fresh, scorched when cold
        if crater.any():
            cm = soft(crater.astype(np.float32))[..., None]
            ht = soft(heat)[..., None]
            scorched = np.array([0.10, 0.07, 0.06]) * (0.7 + 0.6 * self.base.mean(axis=2, keepdims=True))
            molten = np.array([1.0, 0.45, 0.10])
            tex = tex * (1 - cm) + (scorched * (1 - ht) + molten * ht) * cm
        emit = soft(own.astype(np.float32))[..., None] * self.citydots[..., None] * np.array([1.6, 1.2, 0.6])
        if crater.any():
            emit = emit + up(heat)[..., None] * np.array([1.0, 0.4, 0.05]) * 0.8
        return np.clip(tex, 0, 1.5).astype(np.float32), emit.astype(np.float32)

    def shade(self, tex: np.ndarray, emit: np.ndarray, rot: float, cloud_rot: float) -> np.ndarray:
        u = (((self.lon0 + rot) / (2 * math.pi)) * self.tw).astype(np.int32) % self.tw
        uc = (((self.lon0 + cloud_rot) / (2 * math.pi)) * self.tw).astype(np.int32) % self.tw
        col = tex[self.v, u]
        cl = self.cloud[self.v, uc][..., None]
        oc = self.ocean[self.v, u][..., None]
        lit = col * (0.05 + 1.05 * self.light) + self.spec * oc * 0.6
        lit = lit * (1 - cl) + cl * (0.03 + 0.97 * self.light)
        lit += emit[self.v, u] * self.night * (1 - 0.7 * cl) * 1.3
        lit += self.rim * ATMO * self.rim_lit * 0.75
        return np.clip(lit, 0, 1)

    def project(self, x: float, y: float, rot: float, world: World, cx: int, cy: int):
        """Tile (x, y) -> screen (sx, sy, facing) for the current rotation."""
        lat = (0.5 - (y + 0.5) / world.h) * math.pi
        lon = (x + 0.5) / world.w * 2 * math.pi
        rel = lon - rot
        nx = math.cos(lat) * math.sin(rel)
        y2 = -math.sin(lat)
        z2 = math.cos(lat) * math.cos(rel)
        c, s = math.cos(TILT), math.sin(TILT)
        ny = y2 * c + z2 * s
        nz = -y2 * s + z2 * c
        return cx + nx * PLANET_R, cy + ny * PLANET_R, nz


# ---------------- HUD ----------------
def _spaced(d: ImageDraw.ImageDraw, xy, text: str, font, fill, spacing: int = 6):
    widths = [font.getlength(ch) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = xy[0] - total / 2
    for ch, w in zip(text, widths):
        d.text((x, xy[1]), ch, font=font, fill=fill, anchor="lm")
        x += w + spacing


def _wrap(text: str, font, width: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if font.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def _hud(img: Image.Image, world: World, day: int, health: float, headline: str, kind: str, t: float,
         intro: float) -> Image.Image:
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    a = int(255 * intro)
    _spaced(d, (W // 2, 46), "PLANET OF US", F_TITLE, (*TEXT, a), 9)
    d.text((W // 2, 112), f"DAY {day}", font=F_DAY, fill=(*TEXT, a), anchor="mm")

    # headline banner (glass panel with coloured accent)
    if headline:
        col = KIND_COLOR.get(kind, KIND_COLOR["quiet"])
        lines = _wrap(headline, F_BANNER, W - 130)
        bh = 30 + 36 * len(lines)
        top = 178 - int(14 * (1 - min(1, t * 5)))
        al = min(1.0, t * 5)
        d.rounded_rectangle([40, top, W - 40, top + bh], radius=18, fill=(10, 14, 30, int(185 * al)),
                            outline=(*col, int(255 * al)), width=3)
        d.rounded_rectangle([40, top, 52, top + bh], radius=6, fill=(*col, int(255 * al)))
        for i, ln in enumerate(lines):
            d.text((W // 2 + 6, top + 33 + i * 36), ln, font=F_BANNER, fill=(*TEXT, int(255 * al)), anchor="mm")

    # bottom panel
    top = 900
    d.rounded_rectangle([30, top, W - 30, H - 96], radius=22, fill=(8, 12, 26, 170))
    d.text((60, top + 26), "PLANET HEALTH", font=F_SMALL, fill=MUTED, anchor="lm")
    d.text((W - 60, top + 26), f"{health:.0f} / 100", font=F_SMALL, fill=MUTED, anchor="rm")
    d.rounded_rectangle([60, top + 44, W - 60, top + 64], radius=10, fill=(40, 46, 66, 255))
    hc = (90, 220, 130) if health > 50 else ((255, 196, 64) if health > 25 else (255, 80, 60))
    d.rounded_rectangle([60, top + 44, 60 + max(20, (W - 120) * health / 100), top + 64], radius=10, fill=(*hc, 255))
    d.text((60, top + 96), "LARGEST NATIONS", font=F_SMALL, fill=MUTED, anchor="lm")
    for i, n in enumerate(world.leaderboard(5)):
        yy = top + 130 + i * 38
        d.ellipse([60, yy - 9, 78, yy + 9], fill=(*n.color, 255))
        d.text((92, yy), f"{i + 1}. {n.code}", font=F_BODY, fill=TEXT, anchor="lm")
        d.text((W - 60, yy), f"{n.tiles:,} km²", font=F_BODY, fill=TEXT, anchor="rm")

    if world.threat:
        th = world.threat
        pulse = 0.6 + 0.4 * math.sin(t * 12)
        d.text((W // 2, H - 66), f"{THREATS[th['kind']]} INCOMING  ·  {th['need']:,} COMMENTS OR IMPACT",
               font=F_LABEL, fill=(255, 90, 60, int(255 * pulse)), anchor="mm")
    d.text((W // 2, H - 34), "Comment your flag to grow your nation", font=F_SMALL, fill=MUTED, anchor="mm")
    return Image.alpha_composite(img.convert("RGBA"), ov)


# ---------------- one day ----------------
def render_day(globe: Globe, before: Snapshot, world: World, res: DayResult, health_before: float,
               out_mp4: Path, rot_start: float = 0.0, seconds: float = 9.0) -> tuple[Path, float]:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    frames = int(seconds * FPS)
    codes = sorted(world.nations)
    idx = {c: i for i, c in enumerate(codes)}
    colors = np.array([np.array(world.nations[c].color) / 255 for c in codes], np.float32).reshape(-1, 3)
    owner = np.array([[idx[o] if o else -1 for o in row] for row in before.owner], np.int16)
    crater = np.array(before.crater, bool)
    heat = np.zeros(owner.shape, np.float32)
    claimed_at = np.full(owner.shape, -999, np.int32)

    impact_f = int(FPS * 1.8) if res.destroyed else None
    grow_start = (impact_f + int(FPS * 0.6)) if impact_f else int(FPS * 0.9)
    grow_end = int(frames * 0.72)
    headlines = list(zip(res.events, res.kinds)) or [("A quiet day on the planet", "quiet")]
    per_head = frames / len(headlines)

    if impact_f is not None:  # rotate so the impact site faces the camera at the moment of impact
        ix, iy = res.impact_at
        rot_start = (ix + 0.5) / world.w * 2 * math.pi - SPIN * impact_f / FPS
    elif res.new_tiles:      # otherwise aim the camera at where today's growth happens
        ang = [(x + 0.5) / world.w * 2 * math.pi for x, _, _ in res.new_tiles]
        centre = math.atan2(sum(map(math.sin, ang)), sum(map(math.cos, ang)))
        rot_start = centre - SPIN * ((grow_start + grow_end) / 2) / FPS
    timeline: list[tuple[float, str]] = [(0.0, "intro")]
    for i, (_, k) in enumerate(headlines):
        if k not in ("quiet", "hit"):
            timeline.append((i * per_head / FPS + 0.05, k))
    if impact_f is not None:
        timeline += [((impact_f - FPS * 0.8) / FPS, "whoosh"), (impact_f / FPS, "boom")]

    tmp = Path(tempfile.mkdtemp(prefix="pou_"))
    silent = tmp / "video.mp4"
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         str(silent)], stdin=subprocess.PIPE)

    applied, dirty, last_pop = 0, True, -10
    tex = emit = None
    cx0, cy0 = PLANET_C
    last_img = None
    for f in range(frames):
        tsec = f / FPS
        rot = rot_start + SPIN * tsec
        if impact_f is not None and f == impact_f:
            for x, y in res.destroyed:
                owner[y, x] = -1
                crater[y, x] = True
                heat[y, x] = 1.0
            dirty = True
        if impact_f is not None and f > impact_f and heat.max() > 0:
            heat *= 0.975
            dirty = True
        if f >= grow_start:
            target = len(res.new_tiles) if f >= grow_end else \
                int(len(res.new_tiles) * ((f - grow_start) / max(1, grow_end - grow_start)) ** 0.8)
            if target > applied and f - last_pop >= 2:
                timeline.append((tsec, "pop"))
                last_pop = f
            while applied < target:
                x, y, code = res.new_tiles[applied]
                if not crater[y, x]:
                    owner[y, x] = idx[code]
                    claimed_at[y, x] = f
                applied += 1
                dirty = True
        flash = np.clip(1 - (f - claimed_at) / 10.0, 0, 1).astype(np.float32)
        if flash.any():
            dirty = True
        if dirty:
            tex, emit = globe.surface(owner, colors, crater, heat, flash)
            dirty = False

        # camera shake after impact
        cx, cy = cx0, cy0
        if impact_f is not None and impact_f <= f < impact_f + FPS:
            k = 1 - (f - impact_f) / FPS
            cx += int(14 * k * math.sin(f * 2.1))
            cy += int(14 * k * math.cos(f * 1.7))

        frame = globe.bg.copy()
        sphere = globe.shade(tex, emit, rot, rot * 1.18 + 0.6)
        R = PLANET_R
        region = frame[cy - R:cy + R, cx - R:cx + R]
        region[globe.mask] = sphere[globe.mask]
        img = Image.fromarray((frame * 255).astype(np.uint8))
        d = ImageDraw.Draw(img, "RGBA")

        # meteor streak, then shockwave
        if impact_f is not None:
            sx, sy, _ = globe.project(*res.impact_at, rot, world, cx, cy)
            lead = int(FPS * 0.8)
            if impact_f - lead <= f < impact_f:
                p = (f - (impact_f - lead)) / lead
                p = p ** 1.6
                x0, y0 = W + 120, -80
                hx, hy = x0 + (sx - x0) * p, y0 + (sy - y0) * p
                for j in range(14):
                    q = max(0.0, p - j * 0.018)
                    tx, ty = x0 + (sx - x0) * q, y0 + (sy - y0) * q
                    d.line([(hx, hy), (tx, ty)], fill=(255, 200, 120, max(0, 160 - j * 11)), width=max(1, 9 - j // 2))
                d.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=(255, 245, 220, 255))
            if impact_f <= f < impact_f + int(FPS * 1.2):
                k = (f - impact_f) / (FPS * 1.2)
                rr = 20 + 190 * k
                d.ellipse([sx - rr, sy - rr * 0.8, sx + rr, sy + rr * 0.8], outline=(255, 180, 90, int(230 * (1 - k))),
                          width=max(1, int(8 * (1 - k))))
        # monuments
        for mx, my, text, mday in world.monuments:
            px, py, nz = globe.project(mx, my, rot, world, cx, cy)
            if nz < 0.12:
                continue
            al = int(255 * min(1, (nz - 0.12) * 4))
            d.polygon([(px, py - 10), (px - 5, py + 4), (px + 5, py + 4)], fill=(255, 225, 120, al))
            if mday == world.day:
                d.text((px, py - 16), f'"{text}"', font=F_LABEL, fill=(255, 230, 140, al), anchor="md",
                       stroke_width=3, stroke_fill=(0, 0, 0, al))

        if impact_f is not None and impact_f <= f < impact_f + 8:
            img = Image.blend(img, Image.new("RGB", img.size, (255, 244, 230)), 0.85 * (1 - (f - impact_f) / 8))

        hi = min(len(headlines) - 1, int(f // per_head))
        health = health_before + (world.health - health_before) * min(1.0, f / (frames * 0.6))
        img = _hud(img, world, res.day, health, headlines[hi][0], headlines[hi][1],
                   (f - hi * per_head) / per_head, min(1.0, f / 12))
        rgb = img.convert("RGB")
        proc.stdin.write(rgb.tobytes())
        last_img = rgb
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg video encode failed")

    wav = audio.write_wav(tmp / "audio.wav", audio.build(sorted(timeline), seconds, world.health / 100, res.day))
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", str(out_mp4)], check=True)
    last_img.save(out_mp4.with_suffix(".png"))
    shutil.rmtree(tmp, ignore_errors=True)
    return out_mp4, rot_start + SPIN * seconds
