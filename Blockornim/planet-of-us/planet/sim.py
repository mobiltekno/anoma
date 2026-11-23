"""PLANET OF US - world engine.

One planet, shared by everyone who watches. Each day the previous video's numbers
(views, likes, comments) become that day's weather:

  views    -> sunlight: how fast every nation can grow
  likes    -> planet health (health also decays every day; at 0 the planet dies)
  comments -> a flag emoji in a comment is a vote for that nation; votes = growth
  top comment (most likes) -> engraved as a monument on the planet
  threats  -> sometimes an asteroid/plague is announced: the next video needs N
              comments in total, from ALL nations together, or the planet is hit

Nations never attack each other. They race for empty land and only survive
threats together - competition and cooperation at the same time.

The map is equirectangular (width = 2 x height) and wraps east-west, so it can be
wrapped around a rotating sphere. The polar caps are ice and cannot be settled.
"""
from __future__ import annotations

import colorsys
import hashlib
import math
import random
import re
from dataclasses import dataclass, field

import numpy as np

from .noise import fractal

FLAG_RE = re.compile("[\U0001F1E6-\U0001F1FF]{2}")
BLOCKED_WORDS = {"fuck", "shit", "nazi", "kill"}  # placeholder; real list goes in config

THREATS = {
    "asteroid": "ASTEROID",
    "plague": "PLAGUE",
    "ice_age": "ICE AGE",
}

TEX_SCALE = 6          # texture pixels per tile (render detail)
SEA_LEVEL = 0.53
POLAR_ROWS = 0.09      # fraction of rows at each pole that are ice


def flags_in(text: str) -> list[str]:
    """Return ISO-3166 alpha-2 codes for every flag emoji in text (e.g. ['TR', 'BR'])."""
    out = []
    for m in FLAG_RE.finditer(text):
        a, b = m.group(0)
        out.append(chr(ord(a) - 0x1F1E6 + 65) + chr(ord(b) - 0x1F1E6 + 65))
    return out


def nation_color(code: str) -> tuple[int, int, int]:
    h = int(hashlib.sha1(code.encode()).hexdigest()[:6], 16) / 0xFFFFFF
    r, g, b = colorsys.hsv_to_rgb(h, 0.75, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)


def clean_text(text: str, limit: int = 26) -> str | None:
    t = FLAG_RE.sub("", text).strip()
    t = "".join(ch for ch in t if ch.isprintable() and ord(ch) < 0x2000)
    if not t or any(w in t.lower() for w in BLOCKED_WORDS):
        return None
    return t[:limit]


@dataclass
class Nation:
    code: str
    color: tuple[int, int, int]
    joined_day: int
    tiles: int = 0
    votes_total: int = 0
    contacts: set = field(default_factory=set)


@dataclass
class DayResult:
    day: int
    new_tiles: list            # [(x, y, code)] in the order they were claimed
    destroyed: list            # [(x, y)] tiles lost to a threat
    impact_at: tuple | None    # (x, y) centre of the impact, if any
    events: list               # human-readable headlines
    kinds: list                # one tag per headline: nation|contact|monument|warning|saved|hit|death
    votes: dict                # code -> votes today
    threat_resolved: str | None  # "saved" | "hit" | None


class World:
    def __init__(self, height: int = 80, seed: int = 7):
        self.h, self.w = height, height * 2
        self.rng = random.Random(seed)
        self.seed = seed
        self.day = 0
        self.health = 60.0
        self.alive = True
        self.nations: dict[str, Nation] = {}
        self.monuments: list[tuple[int, int, str, int]] = []
        self.threat: dict | None = None
        # terrain lives at texture resolution; the simulation samples it per tile
        self.elevation = fractal(self.h * TEX_SCALE, self.w * TEX_SCALE, seed, octaves=7, base=3)
        centres = self.elevation[TEX_SCALE // 2::TEX_SCALE, TEX_SCALE // 2::TEX_SCALE]
        polar = int(self.h * POLAR_ROWS)
        self.land = [[bool(centres[y, x] > SEA_LEVEL) and polar <= y < self.h - polar
                      for x in range(self.w)] for y in range(self.h)]
        self.owner: list[list[str | None]] = [[None] * self.w for _ in range(self.h)]
        self.crater = [[False] * self.w for _ in range(self.h)]

    # ---------- geometry helpers ----------
    def cells(self):
        for y in range(self.h):
            for x in range(self.w):
                yield x, y

    def _neighbors(self, x: int, y: int):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny = y + dy
            if 0 <= ny < self.h:
                yield (x + dx) % self.w, ny

    def _dist2(self, a, b) -> float:
        dx = abs(a[0] - b[0])
        dx = min(dx, self.w - dx)
        return dx * dx + (a[1] - b[1]) ** 2

    def _free(self, x: int, y: int) -> bool:
        return self.land[y][x] and not self.crater[y][x] and self.owner[y][x] is None

    def free_tiles(self) -> int:
        return sum(self._free(x, y) for x, y in self.cells())

    def _spawn_point(self) -> tuple[int, int] | None:
        cand = [(x, y) for x, y in self.cells() if self._free(x, y)]
        if not cand:
            return None
        # prefer spots far from other nations so everyone gets a fair start
        owned = [(x, y) for x, y in self.cells() if self.owner[y][x]]
        if not owned:
            return self.rng.choice(cand)
        ref = owned[::7] or owned
        sample = self.rng.sample(cand, min(200, len(cand)))
        return max(sample, key=lambda p: min(self._dist2(p, o) for o in ref))

    def _grow(self, code: str, amount: int) -> list:
        claimed = []
        frontier = [(x, y) for x, y in self.cells()
                    if self.owner[y][x] == code and any(self._free(nx, ny) for nx, ny in self._neighbors(x, y))]
        while amount > 0 and frontier:
            x, y = frontier.pop(self.rng.randrange(len(frontier)))
            opts = [(nx, ny) for nx, ny in self._neighbors(x, y) if self._free(nx, ny)]
            if not opts:
                continue
            nx, ny = self.rng.choice(opts)
            self.owner[ny][nx] = code
            claimed.append((nx, ny, code))
            amount -= 1
            frontier.append((nx, ny))
            if len(opts) > 1:
                frontier.append((x, y))
        self.nations[code].tiles += len(claimed)
        return claimed

    def _impact(self, radius: int) -> tuple[list, tuple]:
        mid = [(x, y) for x, y in self.cells() if self.owner[y][x] and 0.25 * self.h <= y <= 0.75 * self.h]
        owned = mid or [(x, y) for x, y in self.cells() if self.owner[y][x]]
        cx, cy = self.rng.choice(owned) if owned else (self.w // 2, self.h // 2)
        lost = []
        for y in range(max(0, cy - radius), min(self.h, cy + radius + 1)):
            for xx in range(cx - radius, cx + radius + 1):
                x = xx % self.w
                if self.land[y][x] and (xx - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                    code = self.owner[y][x]
                    if code:
                        self.nations[code].tiles -= 1
                    self.owner[y][x] = None
                    self.crater[y][x] = True
                    lost.append((x, y))
        self.monuments = [m for m in self.monuments if not self.crater[m[1]][m[0]]]
        return lost, (cx, cy)

    def owner_grid(self) -> np.ndarray:
        """(h, w) int array: -1 = none, else index into sorted(self.nations)."""
        idx = {c: i for i, c in enumerate(sorted(self.nations))}
        return np.array([[idx.get(o, -1) if o else -1 for o in row] for row in self.owner], np.int16)

    # ---------- the daily tick ----------
    def step(self, views: int, likes: int, comments: list[dict], force_threat: str | None = None) -> DayResult:
        """comments: [{'text': str, 'likes': int}] from yesterday's video."""
        if not self.alive:
            raise RuntimeError("the planet is dead")
        self.day += 1
        events, kinds, destroyed, new_tiles, resolved, impact_at = [], [], [], [], None, None

        def say(kind: str, text: str):
            kinds.append(kind)
            events.append(text)

        # 1) settle yesterday's threat
        if self.threat:
            t = self.threat
            if len(comments) >= t["need"]:
                resolved = "saved"
                self.health = min(100.0, self.health + 10)
                say("saved", f"{THREATS[t['kind']]} STOPPED - {len(comments):,}/{t['need']:,} comments")
            else:
                resolved = "hit"
                destroyed, impact_at = self._impact(radius=t["radius"])
                self.health -= 20
                say("hit", f"{THREATS[t['kind']]} HIT - only {len(comments):,}/{t['need']:,}. "
                           f"{len(destroyed)} km² lost")
            self.threat = None

        # 2) health: likes heal, time hurts
        self.health += min(25.0, 8 * math.log10(1 + likes)) - 12
        self.health = max(0.0, min(100.0, self.health))

        # 3) votes -> nations grow
        votes: dict[str, int] = {}
        for c in comments:
            for code in set(flags_in(c["text"])):
                votes[code] = votes.get(code, 0) + 1
        sunlight = 0.5 + math.log10(1 + views) / 5
        arrivals: list[str] = []
        for code in sorted(votes, key=votes.get, reverse=True):
            if code not in self.nations:
                p = self._spawn_point()
                if p is None:
                    continue
                self.nations[code] = Nation(code, nation_color(code), self.day)
                self.owner[p[1]][p[0]] = code
                self.nations[code].tiles = 1
                new_tiles.append((p[0], p[1], code))
                arrivals.append(code)
            n = self.nations[code]
            n.votes_total += votes[code]
            trade = 1 + 0.1 * len(n.contacts)
            new_tiles += self._grow(code, round(sunlight * trade * (3 + 6 * math.sqrt(votes[code]))))
        if arrivals:
            say("nation", f"NEW NATION: {arrivals[0]} landed on the planet" if len(arrivals) == 1 else
                f"{len(arrivals)} NEW NATIONS LANDED: {', '.join(arrivals[:8])}{'...' if len(arrivals) > 8 else ''}")

        # 4) first contacts open trade routes (growth bonus for both)
        pairs: list[str] = []
        for x, y in self.cells():
            a = self.owner[y][x]
            if not a:
                continue
            for nx, ny in self._neighbors(x, y):
                b = self.owner[ny][nx]
                if b and b != a and b not in self.nations[a].contacts:
                    self.nations[a].contacts.add(b)
                    self.nations[b].contacts.add(a)
                    pairs.append(f"{a}+{b}")
        if pairs:
            say("contact", f"FIRST CONTACT: {pairs[0]} opened a trade route" if len(pairs) == 1 else
                f"{len(pairs)} TRADE ROUTES OPENED: {', '.join(pairs[:5])}{'...' if len(pairs) > 5 else ''}")

        # 5) the most-liked comment becomes a monument
        ranked = sorted(comments, key=lambda c: c.get("likes", 0), reverse=True)
        for c in ranked[:5]:
            text = clean_text(c["text"])
            if not text:
                continue
            home = next((f for f in flags_in(c["text"]) if f in self.nations), None)
            spots = [(x, y) for x, y in self.cells() if self.owner[y][x] == home] if home else []
            if spots:
                x, y = self.rng.choice(spots)
                self.monuments.append((x, y, text, self.day))
                say("monument", f'MONUMENT: "{text}"')
            break

        # 6) maybe announce a new threat for tomorrow
        if force_threat or (self.day >= 3 and self.rng.random() < 0.25):
            kind = force_threat or self.rng.choice(list(THREATS))
            need = int(len(comments) * 1.5) + 20
            self.threat = {"kind": kind, "need": need, "radius": 11}
            say("warning", f"WARNING: {THREATS[kind]} in 24h - need {need:,} comments to survive")

        if self.health <= 0:
            self.alive = False
            say("death", "THE PLANET HAS DIED")

        return DayResult(self.day, new_tiles, destroyed, impact_at, events, kinds, votes, resolved)

    def leaderboard(self, n: int = 5) -> list[Nation]:
        return sorted(self.nations.values(), key=lambda k: k.tiles, reverse=True)[:n]
