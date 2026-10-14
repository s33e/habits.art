#!/usr/bin/env python3
"""Build all.habits.art from the Happy Habits library: habits.json + web images, newest first.

Usage:
    python3 build.py --library ../habits-library          # everything
    python3 build.py --library ../habits-library --only 1 # just the newest habit (a quick sample)
Categories come from categories.tsv (number<TAB>category).
"""
import argparse, base64, hashlib, io, json, re, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
SIZE = 600
QUALITY = 82
COPYRIGHT = "Copyright 2022-2026 habits.art. All rights reserved."


def short_hash(data):
    return hashlib.sha1(data).hexdigest()[:10]


def read_habit(p):
    t = p.read_text(encoding="utf-8")
    head, body = t.split("\n---\n", 1)
    get = lambda k: (re.search(rf"\n{k}: (.*)", head) or [None, ""])[1].strip()
    m = re.match(r"\s*## (.*?)\n(.*)", body, re.S)
    paras = [re.sub(r"\s+", " ", x).strip() for x in re.split(r"\n\s*\n", m.group(2)) if x.strip()]
    return {"slug": p.parent.name, "number": int(get("number")), "name": get("name"),
            "date": get("published").split()[0], "lead": re.sub(r"(?<!\.)\.$", "", m.group(1).strip()), "text": paras}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", default=str(ROOT.parent / "habits-library"))
    ap.add_argument("--only", type=int)
    a = ap.parse_args()
    lib = Path(a.library)
    cats = dict(l.split("\t") for l in (ROOT / "categories.tsv").read_text().split("\n") if l)
    habits = sorted((read_habit(p) for p in lib.glob("*/*/habit.md")), key=lambda h: -h["number"])
    habits = [h for h in habits if h["lead"] != "(subtitle)"]
    if a.only: habits = habits[:a.only]
    out = ROOT / "images"; out.mkdir(exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": SIZE, "height": SIZE})
        for h in habits:
            svg = next(lib.glob(f"*/{h['slug']}/drawing.svg")).read_bytes()
            target = out / f"{h['slug']}.webp"
            stamp = out / f".{h['slug']}.src"
            if not (target.exists() and stamp.exists() and stamp.read_text() == short_hash(svg)):
                pg.set_content('<body style="margin:0"><img src="data:image/svg+xml;base64,' + base64.b64encode(svg).decode() + f'" width={SIZE} height={SIZE}>')
                pg.wait_for_timeout(60)
                im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
                exif = Image.Exif(); exif[0x8298] = COPYRIGHT; exif[0x013B] = "habits.art"
                im.save(target, "WEBP", quality=QUALITY, method=6, exif=exif.tobytes())
                stamp.write_text(short_hash(svg))
            h["image"] = f"images/{h['slug']}.webp?v={short_hash(target.read_bytes())}"
            h["category"] = cats.get(str(h["number"]), "")
        b.close()
    keep = {h["slug"] for h in habits}
    if not a.only:
        for f in out.glob("*.webp"):
            if f.stem not in keep: f.unlink()
    (ROOT / "habits.json").write_text(json.dumps(habits, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    html = (ROOT / "index.html").read_text()
    for n in ("style.css", "app.js"):
        html = re.sub(rf'{re.escape(n)}(\?v=[0-9a-f]+)?"', f'{n}?v={short_hash((ROOT / n).read_bytes())}"', html)
    html = re.sub(r'name="data-version" content="[0-9a-f]*"', f'name="data-version" content="{short_hash((ROOT / "habits.json").read_bytes())}"', html)
    (ROOT / "index.html").write_text(html)
    print(f"Built {len(habits)} habits")


if __name__ == "__main__":
    main()
