"""Procedural sound for one day: an ambient space pad plus event sounds placed on a timeline.

No samples, no downloads - every sound is synthesised with numpy, so there is nothing to license.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
PENTA = [0, 2, 4, 7, 9]          # major pentatonic steps (semitones)


def _hz(semi: float, base: float = 220.0) -> float:
    return base * 2 ** (semi / 12)


def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def _lowpass(x: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def _bell(freq: float, dur: float = 1.6, vol: float = 0.25) -> np.ndarray:
    t = _t(dur)
    sig = np.zeros_like(t)
    for ratio, amp, decay in ((1.0, 1.0, 0.9), (2.76, 0.45, 0.45), (5.4, 0.25, 0.2), (8.93, 0.12, 0.1)):
        sig += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / decay)
    attack = np.minimum(1, t / 0.004)
    return vol * sig * attack


def _pop(rng: np.random.Generator) -> np.ndarray:
    t = _t(0.09)
    f = _hz(rng.choice(PENTA) + 12 * rng.integers(1, 3), 330)
    sweep = f * (1 + 0.6 * np.exp(-t / 0.01))
    sig = np.sin(2 * np.pi * np.cumsum(sweep) / SR) * np.exp(-t / 0.025)
    return 0.10 * sig


def _boom(rng: np.random.Generator) -> np.ndarray:
    t = _t(2.6)
    freq = 35 + 95 * np.exp(-t / 0.25)
    sub = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t / 0.9)
    noise = _lowpass(rng.standard_normal(len(t)), 40) * np.exp(-t / 0.5) * 3
    crack = rng.standard_normal(len(t)) * np.exp(-t / 0.03) * 0.6
    return 0.9 * (sub + noise + crack)


def _whoosh(rng: np.random.Generator, dur: float = 0.8) -> np.ndarray:
    t = _t(dur)
    env = (t / dur) ** 2.5
    n = rng.standard_normal(len(t))
    lo = _lowpass(n, 60)
    hi = n - _lowpass(n, 8)
    mix = lo * (1 - t / dur) * 2 + hi * (t / dur) * 0.5
    return 0.5 * mix * env


def _alarm() -> np.ndarray:
    parts = []
    for i in range(6):
        f = 660 if i % 2 == 0 else 520
        t = _t(0.16)
        tone = sum(np.sin(2 * np.pi * f * h * t) / h for h in (1, 3, 5))
        parts.append(0.16 * tone * np.minimum(1, t / 0.01) * np.minimum(1, (0.16 - t) / 0.02))
    return np.concatenate(parts)


def _arpeggio(semis: list[float], base: float, step: float, vol: float) -> np.ndarray:
    out = np.zeros(int((step * len(semis) + 1.8) * SR))
    for i, s in enumerate(semis):
        b = _bell(_hz(s, base), vol=vol)
        i0 = int(i * step * SR)
        out[i0:i0 + len(b)] += b
    return out


def _pad(seconds: float, mood: float, rng: np.random.Generator) -> np.ndarray:
    """mood 0..1 (planet health): low = minor and darker, high = major and brighter."""
    t = _t(seconds)
    chord = [0, 7, 16, 19] if mood > 0.5 else [0, 7, 15, 19]   # major / minor add9-ish
    sig = np.zeros_like(t)
    for s in chord:
        f = _hz(s - 12, 110)
        for detune in (-0.004, 0.0, 0.004):
            ph = rng.random() * 2 * np.pi
            sig += np.sin(2 * np.pi * f * (1 + detune) * t + ph)
            sig += 0.25 * np.sin(2 * np.pi * 2 * f * (1 + detune) * t + ph)
    sig *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.11 * t + rng.random() * 6)
    sig += 0.8 * np.sin(2 * np.pi * 55 * t)                      # sub drone
    bed = np.cumsum(rng.standard_normal(len(t)))                 # brown noise "space wind"
    bed -= _lowpass(bed, 2000)
    sig += 0.02 * bed / (np.abs(bed).max() + 1e-9) * 40
    fade = np.minimum(1, np.minimum(t / 1.0, (seconds - t) / 0.6))
    return 0.035 * sig * np.clip(fade, 0, 1)


def build(timeline: list[tuple[float, str]], seconds: float, mood: float, seed: int = 0) -> np.ndarray:
    """timeline: [(time_sec, kind)], kind in pop|whoosh|boom|nation|contact|monument|warning|saved|hit|death|intro.
    Returns a (n, 2) float32 stereo buffer."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    left = np.zeros(n)
    right = np.zeros(n)
    pad = _pad(seconds, mood, rng)
    left += pad
    right += np.roll(pad, 220)

    def put(t0: float, sig: np.ndarray, pan: float = 0.0):
        i0 = int(t0 * SR)
        if i0 >= n or i0 + len(sig) <= 0:
            return
        s = sig[max(0, -i0): n - i0]
        i0 = max(0, i0)
        left[i0:i0 + len(s)] += s * (1 - max(0, pan))
        right[i0:i0 + len(s)] += s * (1 + min(0, pan))

    for t0, kind in timeline:
        if kind == "pop":
            put(t0, _pop(rng), float(rng.uniform(-0.6, 0.6)))
        elif kind == "whoosh":
            put(t0, _whoosh(rng), -0.3)
        elif kind == "boom":
            put(t0, _boom(rng))
        elif kind == "nation":
            put(t0, _arpeggio([0, 4, 7, 12], 440, 0.09, 0.16))
        elif kind == "contact":
            put(t0, _arpeggio([7, 12], 440, 0.12, 0.14))
        elif kind == "monument":
            put(t0, _arpeggio([0, 7, 12, 16, 19], 330, 0.07, 0.12))
        elif kind == "warning":
            put(t0, _alarm())
        elif kind == "saved":
            put(t0, _arpeggio([0, 4, 7, 12, 16, 19, 24], 330, 0.08, 0.15))
        elif kind == "hit":
            pass                                  # the boom already says it
        elif kind == "death":
            put(t0, _arpeggio([12, 8, 3, 0, -5], 220, 0.35, 0.18))
        elif kind == "intro":
            put(t0, _whoosh(rng, 0.6) * 0.35, 0.3)

    stereo = np.stack([left, right], axis=1)
    stereo = np.tanh(stereo * 1.4) / np.tanh(1.4)        # soft limiter
    peak = np.abs(stereo).max()
    if peak > 0.95:
        stereo *= 0.95 / peak
    return stereo.astype(np.float32)


def write_wav(path: Path, stereo: np.ndarray) -> Path:
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return path
