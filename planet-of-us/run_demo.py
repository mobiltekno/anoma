"""Simulates a 7-day week with fake stats and renders one Short per day.

    python3 run_demo.py            # -> out/day1.mp4 ... out/day7.mp4, out/week.mp4, out/log.md, out/sheet.png
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image

from planet.fake_data import week
from planet.render import Snapshot, render_day
from planet.sim import World

OUT = Path(__file__).parent / "out"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    world = World(seed=11)
    log = ["# PLANET OF US - demo week (fake stats)\n"]
    clips = []
    for stats in week():
        before, hb = Snapshot(world), world.health
        res = world.step(stats["views"], stats["likes"], stats["comments"], stats["force_threat"])
        clip = render_day(before, world, res, hb, OUT / f"day{res.day}.mp4")
        clips.append(clip)
        log.append(f"## Day {res.day}\n- input: {stats['views']:,} views, {stats['likes']:,} likes, "
                   f"{len(stats['comments']):,} comments\n- health: {hb:.0f} -> {world.health:.0f}\n"
                   + "".join(f"- {e}\n" for e in res.events))
        print(f"day {res.day}: {len(res.new_tiles)} new tiles, {len(res.destroyed)} lost, health {world.health:.0f}")
        if not world.alive:
            break

    (OUT / "log.md").write_text("\n".join(log), encoding="utf-8")
    (OUT / "list.txt").write_text("".join(f"file '{c.name}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt",
                    "-c", "copy", "week.mp4"], cwd=OUT, check=True)

    thumbs = [Image.open(c.with_suffix(".png")).resize((270, 480)) for c in clips]
    sheet = Image.new("RGB", (270 * min(4, len(thumbs)), 480 * ((len(thumbs) + 3) // 4)), (8, 10, 22))
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % 4) * 270, (i // 4) * 480))
    sheet.save(OUT / "sheet.png")
    print("done ->", OUT)


if __name__ == "__main__":
    main()
