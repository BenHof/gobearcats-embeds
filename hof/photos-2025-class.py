#!/usr/bin/env python3
"""Replace four 2025-class portraits with playing-era photos from UC's Canto library.

    python3 hof/photos-2025-class.py /path/to/matched-3x4

Ben's review (2026-10-23): Tony Pike's image was a promo graphic with text, KB Sharp's and Tom
Marvaso's needed fixing, and Mike Mickens should be his school photo, not his coaching headshot.
Each source is an Approved Canto asset, cropped to matched 3:4 framing (same face size and eye
line). The script writes 600x800 JPEGs to hof/img/canto/ and points the records in every dashboard
variant at them. The previous images stay in hof/img/ for rollback. Re-running is harmless.
"""
import glob
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "  const DATA = "
BASE_URL = "https://benhof.github.io/gobearcats-embeds/hof/img/canto/"
PHOTOS = {   # name: (matched crop in the scout folder, published file, Canto asset id, what it is)
    "Mike Mickens": ("mickens_2008-photoday_tvhead_canto-plggjaus_matched.jpg", "mike-mickens-2008.jpg",
                     "plggjausi949tdloghb0sedt4o", "2008 football photo day, #21"),
    "Tony Pike": ("pike_2008-photoday_tvhead_canto-eegrvm3n_matched.jpg", "tony-pike-2008.jpg",
                  "eegrvm3nll6vf52nmn9s9dbj0p", "2008 football photo day, #15"),
    "KB Sharp": ("sharp_kb_wbb-mug-color_oldmug_canto-iadugm4p_matched.jpg", "kb-sharp-mug.jpg",
                 "iadugm4p3d751eurpo9mpep43t", "women's basketball color headshot, about 2001-02"),
    "Tom Marvaso": ("marvaso_1973-76_color-portrait-no5_lindas-album_canto-75ejlerr_matched.jpg", "tom-marvaso-no5.jpg",
                    "75ejlerr2l46n18o6k2luika43", "1973-75 color portrait, #5, Nippert Stadium"),
}
DROP = ("image_source_page_url", "image_source_url")


def main():
    src = sys.argv[1]
    out_dir = os.path.join(HERE, "img", "canto")
    for name, (crop, published, _, _) in PHOTOS.items():
        im = Image.open(os.path.join(src, crop)).convert("RGB")
        im = im.resize((600, 800), Image.LANCZOS)
        im.save(os.path.join(out_dir, published), "JPEG", quality=86, optimize=True, progressive=True)

    for path in sorted(glob.glob(os.path.join(HERE, "uc-hof-dashboard*.js"))):
        lines = open(path, encoding="utf-8").read().split("\n")
        idx = next(i for i, l in enumerate(lines) if l.startswith(PREFIX))
        data = json.loads(lines[idx][len(PREFIX):-1])
        hits = [r for r in data["inductees"] if r["name"] in PHOTOS]
        if len(hits) != len(PHOTOS):
            raise SystemExit(f"{os.path.basename(path)}: found {len(hits)} of {len(PHOTOS)} records")
        for r in hits:
            for k in DROP:
                r.pop(k, None)
            r.update({"image_url": BASE_URL + PHOTOS[r["name"]][1], "image_status": "replacement_image_sourced",
                      "image_source": "canto", "image_credit": "gobearcats"})
        lines[idx] = PREFIX + json.dumps(data, ensure_ascii=True, separators=(",", ":")) + ";"
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        print(f"{os.path.basename(path)}: {len(hits)} portraits")

    sources = {name: {"file": "img/canto/" + p[1], "canto_id": p[2], "photo": p[3]} for name, p in PHOTOS.items()}
    with open(os.path.join(out_dir, "photos-2025-class.json"), "w") as f:
        json.dump(sources, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
