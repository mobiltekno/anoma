"""Fake 'yesterday's stats' for a 7-day demo - stands in for the YouTube Data API until the channel exists."""
from __future__ import annotations

import random


def flag(code: str) -> str:
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in code)


# a rough, made-up audience mix; real data comes from comments
POOL = {"US": 20, "BR": 14, "IN": 14, "TR": 9, "ID": 8, "MX": 7, "DE": 5, "PH": 6, "GB": 5, "FR": 4,
        "JP": 3, "KR": 3, "NG": 3, "EG": 3, "AR": 3, "PL": 2, "VN": 3, "PK": 3}

LINES = ["save the planet", "my country is coming", "who else is here from shorts", "day 1 viewer",
         "protect the monument", "we need more comments", "build a bridge", "peace on planet",
         "asteroid can't stop us", "grow grow grow", "hello from home", "this is addictive"]

# (views, likes, comment count, forced threat) per day - a small arc with one failure and one rescue
ARC = [
    (900, 60, 25, None),
    (2_400, 160, 70, None),
    (6_000, 420, 160, "asteroid"),   # announces: tomorrow needs ~260 comments
    (7_500, 380, 190, None),         # not enough -> impact
    (21_000, 1_600, 520, None),      # outrage + sympathy -> growth spike
    (35_000, 2_300, 700, "plague"),  # announces: tomorrow needs ~1,070
    (88_000, 6_100, 1_400, None),    # world unites -> saved
]


def week(seed: int = 3) -> list[dict]:
    rng = random.Random(seed)
    codes, weights = zip(*POOL.items())
    days = []
    for i, (views, likes, n_comments, threat) in enumerate(ARC):
        comments = []
        for _ in range(n_comments):
            parts = []
            if rng.random() < 0.85:
                parts.append(flag(rng.choices(codes, weights)[0]))
            if rng.random() < 0.4:
                parts.append(rng.choice(LINES))
            comments.append({"text": " ".join(parts) or "nice", "likes": int(rng.paretovariate(1.3))})
        days.append({"views": views, "likes": likes, "comments": comments, "force_threat": threat})
    return days
