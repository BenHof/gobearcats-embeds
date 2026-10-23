#!/usr/bin/env python3
"""Copy the public 3D Hall of Fame wall and the 2D wall explorer into hof/wall/ for GitHub Pages.

    python3 hof/wall-sync.py [--source /path/to/serene-pythagoras]

The source workspace builds the pages (generate_3d_wall.py, generate_enhanced_studio.py,
generate_elevation.py) and also holds the wall planning work. This is the public, fan-facing
copy, so the script publishes only what the two pages load once the planning extras are removed:

- wall_3d.html, index.html and docs/HOF_Wall_Elevation.pdf
- master_wall_plaques.json cut to public fields (no evidence, Canto ids, notes or install batches)
- every asset the edited pages reference: plaque atlases, crops, thumbs and production plaques
- production plaque PNGs (0.3-3 MB each) re-encoded as JPEGs at most 1600 px on the long edge,
  with the references rewritten to match

Edits to the pages, each of which must apply exactly once or the run stops:

- The Archibus floor plan dialogs are emptied and the 2D page's Concourse Map button is hidden.
  The floor plans label telecom and electrical rooms and are never copied.
- The 2D page's Concourse Photos gallery (planning evidence) is emptied and its button hidden.
- "Full Bio Page" links point at hof.gobearcats.ai, because a root-relative /inductee/ link
  resolves to benhof.github.io when the page runs in an iframe.
- The 3D page accepts {type: 'uc-hof:plaque', slot} from its parent window, so "Locate on 3D
  Wall" on gobearcats.com/hof flies to a plaque without reloading the scene.

wall/SOURCE.json records the source commit, any uncommitted source changes and a hash of every
published file, so a later run can show what changed.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "wall")
DEFAULT_SOURCE = "/Users/benhofstetter/Documents/antigravity/serene-pythagoras"
PAGES = ["wall_3d.html", "index.html"]
DATA = "master_wall_plaques.json"
PDF = "docs/HOF_Wall_Elevation.pdf"
ASSET_RE = re.compile(r"(?<![\w/.-])((?:web_assets|downloaded_photos|spatial_photos_jpg)/[A-Za-z0-9_./%-]+?\.(?:png|jpe?g|webp|svg|json|pdf))")
EVIDENCE_RE = re.compile(r"const EVIDENCE = (\[.*?\]);\n")
EXCLUDE_PREFIXES = ("web_assets/floor_plans/",)
PUBLIC_SLOT_FIELDS = ["id", "ref_num", "wall", "col", "row", "name", "sport", "plaque_sport_line", "category",
                      "class_year", "inducted", "bio", "image", "thumb"]
# A hash change sent from another origin reloads the iframe, so the embedding page (gobearcats.com/hof)
# posts the plaque instead and the camera flies there in place. Only the direct parent is heard.
MESSAGE_LISTENER = ("addEventListener('message', e => { const d = e.data; "
                    "if (e.source === parent && parent !== window && d && d.type === 'uc-hof:plaque' && SLOT[d.slot]) "
                    "selectSlot(d.slot, true); });\n")
PLAQUE_DIR = "web_assets/production_plaques/"
PLAQUE_EDGE, PLAQUE_QUALITY = 1600, 82


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(source, *args):
    return subprocess.run(["git", "-C", source, *args], capture_output=True, text=True).stdout.strip()


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit(f"{label}: expected 1 match, found {n}. The source page changed; update wall-sync.py.")
    return text.replace(old, new)


def cut_div(text, opening, stub, label):
    """Replace the element that starts with `opening` (through its matching </div>) with `stub`."""
    if text.count(opening) != 1:
        sys.exit(f"{label}: expected 1 match for {opening!r}, found {text.count(opening)}.")
    start = text.index(opening)
    depth = 0
    for m in re.finditer(r"<div\b|</div>", text[start:]):
        depth += 1 if m.group() == "<div" else -1
        if depth == 0:
            return text[:start] + stub + text[start + m.end():]
    sys.exit(f"{label}: no closing </div> found.")


def plaque_jpeg(src, dst):
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    im = im.convert("RGB")
    im.thumbnail((PLAQUE_EDGE, PLAQUE_EDGE), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.save(dst, "JPEG", quality=PLAQUE_QUALITY, optimize=True, progressive=True)


def public_pages(texts):
    w = texts["wall_3d.html"]
    w = cut_div(w, '<div id="spaceplan-modal" hidden>',
                '<div id="spaceplan-modal" hidden><button class="x" id="spaceplan-close" hidden></button></div>',
                "wall_3d.html floor plan dialog")
    w = replace_once(w, 'href="/inductee/${slug}"', 'href="https://hof.gobearcats.ai/inductee/${slug}"',
                     "wall_3d.html bio link")
    hashchange = "addEventListener('hashchange', () => { if (checkPlaqueHash()) return;"
    w = replace_once(w, hashchange, MESSAGE_LISTENER + hashchange, "wall_3d.html plaque messages")
    texts["wall_3d.html"] = w

    x = texts["index.html"]
    x = cut_div(x, '<div class="modal" id="m-space-plan">', '<div class="modal" id="m-space-plan"></div>',
                "index.html floor plan dialog")
    x = replace_once(x, '<button class="btn" id="btn-space-plan"', '<button class="btn" id="btn-space-plan" hidden',
                     "index.html Concourse Map button")
    x = replace_once(x, '<button class="btn" id="btn-evidence"', '<button class="btn" id="btn-evidence" hidden',
                     "index.html Concourse Photos button")
    m = EVIDENCE_RE.search(x)
    if not m:
        sys.exit("index.html photo gallery: const EVIDENCE not found.")
    x = x[:m.start(1)] + "[]" + x[m.end(1):]
    texts["index.html"] = x

    data = json.loads(texts[DATA])
    data = {"walls": data["walls"],
            "slots": [{k: s[k] for k in PUBLIC_SLOT_FIELDS if k in s} for s in data["slots"]]}
    texts[DATA] = json.dumps(data, ensure_ascii=False, indent=1)
    return texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    source = ap.parse_args().source

    texts = public_pages({p: open(os.path.join(source, p), encoding="utf-8").read() for p in PAGES + [DATA]})
    assets = sorted({m.group(1) for t in texts.values() for m in ASSET_RE.finditer(t)})
    leaked = [a for a in assets if a.startswith(EXCLUDE_PREFIXES)]
    if leaked:
        sys.exit(f"Edited pages still reference excluded files: {leaked}")
    missing = [a for a in assets if not os.path.exists(os.path.join(source, a))]
    if missing:
        sys.exit(f"Referenced but missing in the source: {missing[:10]}")

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "docs"))

    renames = {}
    for a in assets:
        src = os.path.join(source, a)
        if a.startswith(PLAQUE_DIR) and a.lower().endswith(".png"):
            renames[a] = a[:-4] + ".jpg"
            plaque_jpeg(src, os.path.join(OUT, renames[a]))
        else:
            os.makedirs(os.path.dirname(os.path.join(OUT, a)), exist_ok=True)
            shutil.copy2(src, os.path.join(OUT, a))

    for p, t in texts.items():
        for old, new in renames.items():
            t = t.replace(old, new)
        with open(os.path.join(OUT, p), "w", encoding="utf-8") as f:
            f.write(t)
    shutil.copy2(os.path.join(source, PDF), os.path.join(OUT, PDF))

    files = {}
    for root, _, names in os.walk(OUT):
        for n in sorted(names):
            path = os.path.join(root, n)
            files[os.path.relpath(path, OUT)] = {"bytes": os.path.getsize(path), "sha256": sha256(path)}
    dirty = [l[3:] for l in git(source, "status", "--porcelain").splitlines() if l[3:] in PAGES + [DATA, PDF]]
    manifest = {
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "source_branch": git(source, "rev-parse", "--abbrev-ref", "HEAD"),
        "source_commit": git(source, "rev-parse", "HEAD"),
        "source_uncommitted": dirty,
        "plaques_reencoded": f"{len(renames)} PNG to JPEG, <= {PLAQUE_EDGE} px, q{PLAQUE_QUALITY}",
        "total_bytes": sum(v["bytes"] for v in files.values()),
        "files": dict(sorted(files.items())),
    }
    with open(os.path.join(OUT, "SOURCE.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"{len(files)} files, {manifest['total_bytes'] / 1e6:.1f} MB in {OUT}; re-encoded {len(renames)} plaques")
    if dirty:
        print(f"note: the source has uncommitted changes in {dirty}")


if __name__ == "__main__":
    main()
