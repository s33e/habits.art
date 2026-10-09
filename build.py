#!/usr/bin/env python3
"""Build habits.json and web images from the Happy Habits library.

Usage:
    python3 build.py                      # library cloned/updated automatically
    python3 build.py --library ../habits-library

The selection lives in habits.txt: one slug per line, in grid order.
Lines starting with # are ignored.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
LIBRARY_REPO = "https://github.com/s33e/habits-library"
IMAGE_SIZE = 1200          # px, square
IMAGE_QUALITY = 86         # webp
COPYRIGHT = "Copyright 2022-2026 habits.art. All rights reserved."   # written into every image file (plain ASCII, as EXIF requires)

# Leading emoji / symbols at the start of a description ("🚁  When in doubt...")
LEADING_SYMBOLS = re.compile(r"^[^\w\"'“‘(]+", re.UNICODE)


def short_hash(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()[:10]


def stamp_versions():
    """Give style.css, app.js and habits.json a content stamp (?v=...) in index.html,
    so a browser always gets the page and its styling/data as a matching set."""
    index = ROOT / "index.html"
    html = index.read_text(encoding="utf-8")
    for name in ("style.css", "app.js"):
        html = re.sub(rf'{re.escape(name)}(\?v=[0-9a-f]+)?"', f'{name}?v={short_hash(ROOT / name)}"', html)
    data_v = short_hash(ROOT / "habits.json")
    html = re.sub(r'<meta name="data-version" content="[0-9a-f]*">', f'<meta name="data-version" content="{data_v}">', html)
    index.write_text(html, encoding="utf-8")


def get_library(path_arg):
    lib = Path(path_arg).resolve() if path_arg else ROOT.parent / "habits-library"
    if not lib.exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", LIBRARY_REPO, str(lib)], check=True)
    elif not path_arg and (lib / ".git").exists():
        subprocess.run(["git", "-C", str(lib), "pull", "-q"], check=False)
    return lib


def read_habit(lib, slug):
    """Find <year>/<slug>/habit.md in the library and return (folder, name, lead, paragraphs)."""
    hits = sorted(lib.glob(f"*/{slug}/habit.md"))
    if not hits:
        return None
    t = hits[0].read_text(encoding="utf-8")
    head, body = t.split("\n---\n", 1)
    name = re.search(r"\nname: (.*)", head).group(1).strip()
    m = re.match(r"\s*## (.*?)\n(.*)", body, re.S)
    lead, rest = m.group(1).strip(), m.group(2)
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", rest) if p.strip()]
    return hits[0].parent, name, re.sub(r"(?<!\.)\.$", "", lead), paras


def render(svg, target):
    import base64, io
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": IMAGE_SIZE, "height": IMAGE_SIZE})
        pg.set_content('<body style="margin:0"><img src="data:image/svg+xml;base64,' + base64.b64encode(svg.read_bytes()).decode() + f'" width={IMAGE_SIZE} height={IMAGE_SIZE}>')
        pg.wait_for_timeout(150); png = pg.screenshot(); b.close()
    im = Image.open(io.BytesIO(png)).convert("RGB")
    exif = Image.Exif(); exif[0x8298] = COPYRIGHT; exif[0x013B] = "habits.art"
    im.save(target, "WEBP", quality=IMAGE_QUALITY, method=6, exif=exif.tobytes())


def read_selection():
    lines = (ROOT / "habits.txt").read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library")
    args = ap.parse_args()

    lib = get_library(args.library)
    selection = read_selection()
    found = {slug: read_habit(lib, slug) for slug in selection}
    problems = [f"{s}: not in the library" for s, h in found.items() if not h]
    problems += [f"{s}: no text yet" for s, h in found.items() if h and h[2] == "(subtitle)"]
    if len(set(selection)) != len(selection):
        problems.append("habits.txt lists the same slug twice")
    if problems:
        sys.exit("Fix habits.txt first:\n  " + "\n  ".join(problems))

    out_dir = ROOT / "images"
    out_dir.mkdir(exist_ok=True)
    habits = []
    for slug in selection:
        folder, name, lead, paras = found[slug]
        target = out_dir / f"{slug}.webp"
        render(folder / "drawing.svg", target)
        habits.append({"slug": slug, "name": name, "image": f"images/{slug}.webp?v={short_hash(target)}", "lead": lead, "text": paras})

    # drop images of habits that are no longer selected
    keep = {f"{s}.webp" for s in selection}
    for f in out_dir.glob("*.webp"):
        if f.name not in keep:
            f.unlink()

    (ROOT / "habits.json").write_text(json.dumps(habits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    stamp_versions()
    print(f"Built {len(habits)} habits:")
    for h in habits:
        print(f"  {h['name']}  ({len(h['lead']) + sum(len(p) for p in h['text'])} chars)")


if __name__ == "__main__":
    main()
