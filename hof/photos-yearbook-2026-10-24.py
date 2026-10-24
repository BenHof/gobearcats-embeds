#!/usr/bin/env python3
"""Portraits for the last two Hall of Famers who showed initials, from UC's own yearbook.

    python3 hof/photos-yearbook-2026-10-24.py ~/LLM-Wiki_mbp/outputs/HOF-3DWall/photo-audit-2026-10-23/yearbook

Canto has no photo of Carol Brestel or Hap Glaser. Both are senior portraits in The Cincinnatian,
digitized by UC Libraries in the OhioLINK Digital Resource Commons (rights holder: University of
Cincinnati), found by full-text search and checked against the page's caption order:
  - Carol Brestel, Teachers College 1941 (W.A.A. President, Mortar Board), 1941 volume, PDF page 53
  - Rose Mary "Hap" Glaser, Teachers College 1943 (Arete, W.A.A.), 1943 volume, PDF page 88
The 600 dpi crops, the full pages and the 3:4 crops are in the wiki folder passed in. The script
writes 600x800 JPEGs to hof/img/canto/ and points the records in every dashboard variant at them,
credited to the yearbook. Re-running is harmless.
"""
import glob
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "  const DATA = "
BASE_URL = "https://benhof.github.io/gobearcats-embeds/hof/img/canto/"
PHOTOS = {   # name: (3:4 crop in the wiki folder, published file, credit, DRC item)
    "Carol Brestel": ("brestel_carol_1941-cincinnatian_matched.jpg", "carol-brestel-1941-cincinnatian.jpg",
                      "The Cincinnatian, 1941 (UC Libraries)",
                      "https://drc.libraries.uc.edu/items/ffa6b408-e9f2-478c-af8f-9dcc4b4b501c"),
    "Hap Glaser": ("glaser_hap_1943-cincinnatian_matched.jpg", "hap-glaser-1943-cincinnatian.jpg",
                   "The Cincinnatian, 1943 (UC Libraries)",
                   "https://drc.libraries.uc.edu/items/dc19e2f0-db01-4e98-8273-c0190a0d59af"),
}
DROP = ("image_source_page_url", "image_source_url")


def main():
    src = sys.argv[1]
    out_dir = os.path.join(HERE, "img", "canto")
    for name, (crop, published, _, _) in PHOTOS.items():
        shutil.copyfile(os.path.join(src, crop), os.path.join(out_dir, published))

    for path in sorted(glob.glob(os.path.join(HERE, "uc-hof-dashboard*.js"))):
        lines = open(path, encoding="utf-8").read().split("\n")
        idx = next(i for i, l in enumerate(lines) if l.startswith(PREFIX))
        data = json.loads(lines[idx][len(PREFIX):-1])
        hits = [r for r in data["inductees"] if r["name"] in PHOTOS]
        if sorted(r["name"] for r in hits) != sorted(PHOTOS):
            raise SystemExit(f"{os.path.basename(path)}: found {len(hits)} records for {len(PHOTOS)} names")
        for r in hits:
            for k in DROP:
                r.pop(k, None)
            r.update({"image_url": BASE_URL + PHOTOS[r["name"]][1], "image_status": "replacement_image_sourced",
                      "image_source": "uc_yearbook", "image_credit": PHOTOS[r["name"]][2]})
        lines[idx] = PREFIX + json.dumps(data, ensure_ascii=True, separators=(",", ":")) + ";"
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        print(f"{os.path.basename(path)}: {len(hits)} portraits")

    sources = {name: {"file": "img/canto/" + p[1], "credit": p[2], "drc_item": p[3]} for name, p in PHOTOS.items()}
    with open(os.path.join(out_dir, "photos-yearbook-2026-10-24.json"), "w") as f:
        json.dump(sources, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
