#!/usr/bin/env python3
"""UC-era yearbook portraits for nine Hall of Famers whose photos were weak (approved by Ben 2026-10-26).

    python3 hof/photos-yearbook-2026-10-26.py ~/LLM-Wiki_mbp/outputs/HOF-3DWall/photo-audit-2026-10-23/yearbook

The current photos were pro-era (Koufax), signed across the face (Pease, Gillman, Joe Miller), soft action
or card scans (Allen, Bryant, Holstein, Shundich) or later in life (Weil). Each replacement is a captioned
portrait in The Cincinnatian (UC Libraries Digital Resource Commons; rights holder University of
Cincinnati), and identity is proven on the page itself; SOURCES.md in the wiki folder records how for each
person. The script writes 600x800 JPEGs to hof/img/canto/ under new names (previous images stay for
rollback) and points the records in every dashboard variant at them, credited to the yearbook.
"""
import glob
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "  const DATA = "
BASE_URL = "https://benhof.github.io/gobearcats-embeds/hof/img/canto/"
DRC = "https://drc.libraries.uc.edu/items/"
PHOTOS = {   # name: (3:4 crop in the wiki folder, published file, credit, DRC item)
    "Sandy Koufax": ("koufax_sandy_1954-cincinnatian_matched.jpg", "sandy-koufax-1954-cincinnatian.jpg",
                     "The Cincinnatian, 1954 (UC Libraries)", DRC + "c186302e-1083-49f8-8d8f-5d815d3929e9"),
    "Ethan Allen": ("allen_ethan_1927-cincinnatian_matched.jpg", "ethan-allen-1927-cincinnatian.jpg",
                    "The Cincinnatian, 1927 (UC Libraries)", DRC + "ffc90ed1-4a4a-4f34-990f-86e4fcb32614"),
    "John Pease": ("pease_john_1926-cincinnatian_matched.jpg", "john-pease-1926-cincinnatian.jpg",
                   "The Cincinnatian, 1926 (UC Libraries)", DRC + "a50f25e7-ae1b-40f9-9d44-85928b844c07"),
    "Sid Gillman": ("gillman_sid_1951-cincinnatian_matched.jpg", "sid-gillman-1951-cincinnatian.jpg",
                    "The Cincinnatian, 1951 (UC Libraries)", DRC + "a3017424-a922-430a-9df4-1f51a8f87cd3"),
    "Joe Miller": ("miller_joe_1956-cincinnatian_matched.jpg", "joe-miller-1956-cincinnatian.jpg",
                   "The Cincinnatian, 1956 (UC Libraries)", DRC + "22902704-80ee-45b4-8cc8-552ce465ee10"),
    "Nick Shundich": ("shundich_nick_1951-cincinnatian_matched.jpg", "nick-shundich-1951-cincinnatian.jpg",
                      "The Cincinnatian, 1951 (UC Libraries)", DRC + "a3017424-a922-430a-9df4-1f51a8f87cd3"),
    "Jim Holstein": ("holstein_jim_1952-cincinnatian_matched.jpg", "jim-holstein-1952-cincinnatian.jpg",
                     "The Cincinnatian, 1952 (UC Libraries)", DRC + "5d975fb0-6d32-4fda-9570-21582922f3c3"),
    "Richard Bryant": ("bryant_richard_1928-cincinnatian_matched.jpg", "richard-bryant-1928-cincinnatian.jpg",
                       "The Cincinnatian, 1928 (UC Libraries)", DRC + "a00b06df-7f98-4d68-8a73-d09ae32da6ed"),
    "Olga Weil": ("weil_olga_1925-cincinnatian_matched.jpg", "olga-weil-1925-cincinnatian.jpg",
                  "The Cincinnatian, 1925, as Olga Strashun (UC Libraries)", DRC + "d211c2c4-73e9-4705-b454-49bee57c8576"),
}
DROP = ("image_source_page_url", "image_source_url")


def main():
    src = sys.argv[1]
    out_dir = os.path.join(HERE, "img", "canto")
    for name, (crop, published, _, _) in PHOTOS.items():
        dst = os.path.join(out_dir, published)
        if os.path.exists(dst) and open(dst, "rb").read() != open(os.path.join(src, crop), "rb").read():
            raise SystemExit(f"{published} already exists with other content; pick another name")
        shutil.copyfile(os.path.join(src, crop), dst)

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
    with open(os.path.join(out_dir, "photos-yearbook-2026-10-26.json"), "w") as f:
        json.dump(sources, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
