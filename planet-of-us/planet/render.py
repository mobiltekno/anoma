"""Turns one simulated day into a vertical Short (540x960 frames -> mp4 via ffmpeg)."""
from __future__ import annotations

import copy
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .sim import THREATS, DayResult, World

W, H = 540, 960
FPS = 24
BG = (8, 10, 22)
OCEAN = (18, 42, 84)
LAND = (52, 64, 58)
CRATER = (28, 22, 20)
TEXT = (235, 238, 245)
MUTED = (150, 158, 175)
ALERT = (255, 92, 72)
GOOD = (96, 220, 140)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def _font(size: int, bold: bool = True):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(str(FONT_DIR / name), size)
    except OSError:
        return ImageFont.load_default(size)


F_TITLE, F_DAY, F_BODY, F_SMALL, F_BANNER = _font(30), _font(54), _font(20, False), _font(16, False), _font(22)

PLANET_R = 210
PLANET_C = (W // 2, 434)


class Snapshot:
    """Frozen copy of the world grid, so frames can be drawn mid-animation."""

    def __init__(self, world: World):
        self.size = world.size
        self.land = world.land
        self.owner = copy.deepcopy(world.owner)
        self.crater = copy.deepcopy(world.crater)
        self.colors = {c: n.color for c, n in world.nations.items()}


def _planet_layer(snap: Snapshot, shake: float = 0.0) -> Image.Image:
    cell = (PLANET_R * 2) / snap.size
    img = Image.new("RGB", (PLANET_R * 2, PLANET_R * 2), BG)
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, PLANET_R * 2 - 1, PLANET_R * 2 - 1], fill=OCEAN)
    for y in range(snap.size):
        for x in range(snap.size):
            if not snap.land[y][x]:
                continue
            if snap.crater[y][x]:
                col = CRATER
            elif snap.owner[y][x]:
                col = snap.colors.get(snap.owner[y][x], LAND)
            else:
                col = LAND
            d.rectangle([x * cell, y * cell, (x + 1) * cell, (y + 1) * cell], fill=col)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, PLANET_R * 2 - 1, PLANET_R * 2 - 1], fill=255)
    out = Image.new("RGB", img.size, BG)
    out.paste(img, (0, 0), mask)
    return out


def _wrap(text: str, font, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _hud(img: Image.Image, world: World, res: DayResult, health: float, banner: str | None, t: float):
    d = ImageDraw.Draw(img)
    d.text((W // 2, 34), "PLANET OF US", font=F_TITLE, fill=TEXT, anchor="mm")
    d.text((W // 2, 92), f"DAY {res.day}", font=F_DAY, fill=TEXT, anchor="mm")

    # health bar
    y = 650
    d.text((40, y), "PLANET HEALTH", font=F_SMALL, fill=MUTED)
    d.rounded_rectangle([40, y + 24, W - 40, y + 42], radius=9, fill=(40, 44, 60))
    col = GOOD if health > 50 else ((255, 196, 64) if health > 25 else ALERT)
    d.rounded_rectangle([40, y + 24, 40 + max(18, (W - 80) * health / 100), y + 42], radius=9, fill=col)
    d.text((W - 40, y), f"{health:.0f}/100", font=F_SMALL, fill=MUTED, anchor="ra")

    # leaderboard
    y = 712
    d.text((40, y), "LARGEST NATIONS", font=F_SMALL, fill=MUTED)
    for i, n in enumerate(world.leaderboard(5)):
        yy = y + 26 + i * 26
        d.rectangle([40, yy + 3, 56, yy + 19], fill=n.color)
        d.text((66, yy), f"{n.code}", font=F_BODY, fill=TEXT)
        d.text((W - 40, yy), f"{n.tiles:,} km²", font=F_BODY, fill=TEXT, anchor="ra")

    # banner (one headline at a time, fades in)
    if banner:
        alert = any(k in banner for k in ("HIT", "WARNING", "DIED"))
        lines = _wrap(banner, F_BANNER, W - 80)
        bh = 22 + 28 * len(lines)
        top = 138
        a = min(1.0, t * 4)
        fill = tuple(int(c * a) for c in (ALERT if alert else (40, 120, 255)))
        d.rounded_rectangle([30, top, W - 30, top + bh], radius=14, fill=fill)
        for i, ln in enumerate(lines):
            d.text((W // 2, top + 24 + i * 28), ln, font=F_BANNER, fill=TEXT, anchor="mm")

    # call to action / threat countdown
    if world.threat:
        th = world.threat
        msg = f"{THREATS[th['kind']]} INCOMING - {th['need']:,} COMMENTS OR IMPACT"
        d.text((W // 2, H - 58), msg, font=F_SMALL, fill=ALERT, anchor="mm")
    d.text((W // 2, H - 30), "Comment your flag to grow your nation", font=F_SMALL, fill=MUTED, anchor="mm")


def render_day(before: Snapshot, world: World, res: DayResult, health_before: float,
               out_mp4: Path, seconds: float = 8.0) -> Path:
    """Animate before -> after: new land appears tile by tile, impacts flash, headlines cycle."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    frames = int(seconds * FPS)
    tmp = Path(tempfile.mkdtemp(prefix="pou_"))
    snap = copy.copy(before)
    snap.owner = copy.deepcopy(before.owner)
    snap.crater = copy.deepcopy(before.crater)
    snap.colors = {c: n.color for c, n in world.nations.items()}

    impact_frames = range(int(FPS * 0.8), int(FPS * 1.6)) if res.destroyed else range(0)
    grow_start = int(FPS * 1.6) if res.destroyed else int(FPS * 0.5)
    grow_end = int(frames * 0.75)
    headlines = res.events or ["A quiet day on the planet"]
    per_headline = max(1, frames // len(headlines))
    applied = 0
    planet = _planet_layer(snap)
    dirty = True

    for f in range(frames):
        if res.destroyed and f == impact_frames.start:
            for x, y in res.destroyed:
                snap.owner[y][x] = None
                snap.crater[y][x] = True
            dirty = True
        if grow_start <= f:
            target = len(res.new_tiles) if f >= grow_end else int(len(res.new_tiles) * (f - grow_start) / max(1, grow_end - grow_start))
            while applied < target:
                x, y, code = res.new_tiles[applied]
                if not snap.crater[y][x]:
                    snap.owner[y][x] = code
                applied += 1
                dirty = True
        if dirty:
            planet = _planet_layer(snap)
            dirty = False

        img = Image.new("RGB", (W, H), BG)
        ox, oy = PLANET_C[0] - PLANET_R, PLANET_C[1] - PLANET_R
        if f in impact_frames:
            k = (f - impact_frames.start) / max(1, len(impact_frames))
            ox += int(10 * math.sin(f * 2.3) * (1 - k))
            oy += int(10 * math.cos(f * 1.7) * (1 - k))
        img.paste(planet, (ox, oy))
        if f in impact_frames and f - impact_frames.start < 4:
            img = Image.blend(img, Image.new("RGB", (W, H), (255, 240, 220)), 0.7)

        # monuments: small markers + latest label
        d = ImageDraw.Draw(img)
        cell = (PLANET_R * 2) / world.size
        for mx, my, text, mday in world.monuments:
            px, py = ox + mx * cell + cell / 2, oy + my * cell + cell / 2
            d.polygon([(px, py - 7), (px - 4, py + 3), (px + 4, py + 3)], fill=(255, 230, 120))
            if mday == res.day:
                d.text((px, py - 12), f'"{text}"', font=F_SMALL, fill=(255, 230, 120), anchor="md")

        p = f / frames
        health = health_before + (world.health - health_before) * min(1.0, p * 1.5)
        hi = min(len(headlines) - 1, f // per_headline)
        _hud(img, world, res, health, headlines[hi], (f % per_headline) / per_headline)
        img.save(tmp / f"f{f:04d}.png")

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", str(out_mp4)], check=True)
    last = Image.open(tmp / f"f{frames - 1:04d}.png").copy()
    shutil.rmtree(tmp, ignore_errors=True)
    last.save(out_mp4.with_suffix(".png"))
    return out_mp4
