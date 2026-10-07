#!/usr/bin/env python3
"""Build habits.json and web images from the Happy Habits library.

Usage:
    python3 build.py                      # library cloned/updated automatically
    python3 build.py --library ../happyhabits-site

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
LIBRARY_REPO = "https://github.com/s33e/happyhabits-site"
IMAGE_SIZE = 1200          # px, square
IMAGE_QUALITY = 86         # webp

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
    if path_arg:
        lib = Path(path_arg).resolve()
    else:
        lib = ROOT.parent / "happyhabits-site"
        if (lib / ".git").exists():
            subprocess.run(["git", "-C", str(lib), "pull", "-q"], check=False)
        else:
            subprocess.run(["git", "clone", "-q", "--depth", "1", LIBRARY_REPO, str(lib)], check=True)
    if not (lib / "habits.csv").exists():
        sys.exit(f"No habits.csv in {lib}")
    return lib


def clean_text(raw):
    text = raw.split(" // ")[0]                 # some entries hold a second, longer version after //
    text = LEADING_SYMBOLS.sub("", text.strip())
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [re.sub(r"\s+", " ", p) for p in paragraphs]


SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "vs"}


def clean_name(raw):
    name = re.split(r"\s+-{2,}", raw)[0]          # "Keep Learning ---- (formerly Learn)" -> "Keep Learning"
    name = re.sub(r"\s+", " ", name).strip()
    words = name.split(" ")
    out = []
    for i, w in enumerate(words):
        if i > 0 and w.lower() in SMALL_WORDS and not words[i - 1].endswith(")"):
            out.append(w.lower())
        elif w[:1].islower():
            out.append(w[:1].upper() + w[1:])
        else:
            out.append(w)
    return " ".join(out)


def split_lead(paragraphs):
    """First sentence becomes the bold lead; the rest stays as body paragraphs."""
    first = paragraphs[0]
    m = re.match(r"^(.+?[.!?])\s+(.+)$", first, re.S)
    if not m:
        return first, paragraphs[1:]
    return m.group(1), [m.group(2)] + paragraphs[1:]


def read_selection():
    lines = (ROOT / "habits.txt").read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library")
    args = ap.parse_args()

    lib = get_library(args.library)
    rows = {r["slug"]: r for r in csv.DictReader(open(lib / "habits.csv", encoding="utf-8"))}
    selection = read_selection()

    problems = []
    for slug in selection:
        if slug not in rows:
            problems.append(f"{slug}: not in habits.csv")
        elif not (lib / "images" / f"{slug}.jpg").exists():
            problems.append(f"{slug}: no drawing in images/")
        elif len(clean_text(rows[slug]["description"])) == 0:
            problems.append(f"{slug}: no text")
    if len(set(selection)) != len(selection):
        problems.append("habits.txt lists the same slug twice")
    if problems:
        sys.exit("Fix habits.txt first:\n  " + "\n  ".join(problems))

    out_dir = ROOT / "images"
    out_dir.mkdir(exist_ok=True)
    habits = []
    for slug in selection:
        row = rows[slug]
        target = out_dir / f"{slug}.webp"
        if not target.exists():
            im = Image.open(lib / "images" / f"{slug}.jpg").convert("RGB")
            im = im.resize((IMAGE_SIZE, IMAGE_SIZE), Image.LANCZOS)
            im.save(target, "WEBP", quality=IMAGE_QUALITY, method=6)
        habits.append({
            "slug": slug,
            "name": clean_name(row["name"]),
            "image": f"images/{slug}.webp?v={short_hash(target)}",
            "lead": split_lead(clean_text(row["description"]))[0],
            "text": split_lead(clean_text(row["description"]))[1],
        })

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
