"""Seamless (horizontally wrapping) fractal noise for an equirectangular planet map."""
from __future__ import annotations

import numpy as np
from PIL import Image


def fractal(h: int, w: int, seed: int, octaves: int = 6, base: int = 4, persistence: float = 0.5) -> np.ndarray:
    """Return an (h, w) float32 array in [0, 1] that tiles seamlessly left-right."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        gw = base * 2 ** o
        gh = max(2, gw // 2)
        grid = rng.random((gh, gw)).astype(np.float32)
        tiled = np.concatenate([grid, grid, grid], axis=1)          # wrap in x
        img = Image.fromarray(tiled).resize((w * 3, h), Image.BICUBIC)
        out += amp * np.asarray(img, np.float32)[:, w:2 * w]
        total += amp
        amp *= persistence
    out /= total
    out -= out.min()
    out /= max(1e-6, out.max())
    return out
