#!/usr/bin/env python3
"""Apply the portraits Ben approved from the 2026-10-23 photo audit.

    python3 hof/photos-audit-2026-10-23.py ~/LLM-Wiki_mbp/outputs/HOF-3DWall/photo-audit-2026-10-23/matched-3x4

The audit (wiki outputs/HOF-3DWall/photo-audit-2026-10-23/AUDIT.md) flagged 118 of 225 portraits and
sorted Canto replacements into tiers. Ben approved (2026-10-23) the four records that showed initials
and had a candidate, and tier 2: a different, better photo where the current one is game action, a
graphic, a full-length shot or a later-life photo of an athlete. Every source is a Canto
asset, cropped to the same 3:4 framing as the Mickens/Pike/Sharp/Marvaso fix. The script writes
600x800 JPEGs to hof/img/canto/ and points the records in every dashboard variant at them. Previous
images stay in hof/img/ for rollback. Re-running is harmless.
"""
import glob
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "  const DATA = "
BASE_URL = "https://benhof.github.io/gobearcats-embeds/hof/img/canto/"
# Class of 2026 rows are review-manifest additions; verify-content.py accepts their portraits only as
# primary_image_present from Canto or GoBearcats.
ADDITIONS = {"Bob Huggins"}
PHOTOS = {   # name: (matched crop in the audit folder, published file, Canto asset id, what it is)
    # Showed initials
    "Ike Stewart": ("stewart_ike_1919-varsity-club-group_matched.jpg", "ike-stewart-1919.jpg",
                    "6fbdl4o8h96mh9gm8glf85vi48", "1919 yearbook varsity club photo; identified by caption order"),
    "Robert Miller": ("miller_bob_mbb-portrait_matched.jpg", "robert-miller-mbb.jpg",
                      "f9r505vs0d257dpfcmsnsuu265", "men's basketball portrait (not the football #76 in the HOF Members album)"),
    "Miriam Merrill": ("merrill_mimi_2001-weight-throw-action_matched.jpg", "miriam-merrill-2001.jpg",
                       "qb65adf32979f8v0m0a8ki9h06", "2001 weight throw; best available"),
    "Ron Stapleton": ("stapleton_ron_1973-tri-captains-crop_matched.jpg", "ron-stapleton-1973.jpg",
                      "ohle6sqfi16bf0h1119df0vj2m", "1973 tri-captains photo"),
    # Tier 2: a different, better photo
    "Bob Huggins": ("huggins_bob_2001-02-coach-headshot_matched.jpg", "bob-huggins-coach.jpg",
                    "0bmovk2q1d3812gtda3anmr23q", "coaching-era headshot"),
    "Ann Thomas": ("thomas_ann_2001-mug-color_matched.jpg", "ann-thomas-2001.jpg",
                   "av8028cacl44b56bn3gu1daf1l", "2001 color mug"),
    "Andrew Kean": ("kean_andrew_msoc-headshot_matched.jpg", "andrew-kean-msoc.jpg",
                    "u59d4hbgnp6e9386jj6d918a46", "men's soccer headshot"),
    "Jason Fabini": ("fabini_jason_1996-no67-color_matched.jpg", "jason-fabini-1996.jpg",
                     "nunlg4jg9t31d0ktco0mush774", "1996 color portrait, #67"),
    "John Wiethe": ("wiethe_john_suit-portrait_matched.jpg", "john-wiethe-suit.jpg",
                    "cos0u9f3ol7o7d1hqb8t0lqe04", "suit portrait"),
    "Mike Gates": ("gates_mike_gates-3-copy_matched.jpg", "mike-gates.jpg",
                   "ohff6ss5k151l0q2uup1liqm1d", "jersey portrait without the caption"),
    "Lewis Johnson": ("johnson_lewis_johnson-lewis-2-copy_matched.jpg", "lewis-johnson.jpg",
                      "a04ml95acl7dncu08pnhic7137", "track singlet portrait"),
    "Tay Baker": ("baker_tay_image-389_matched.jpg", "tay-baker-playing.jpg",
                  "5q4ml9d0qt0a3a8p7490gjfn4r", "playing era, #22 with ball"),
    "Gene Ruehlmann": ("ruehlmann_gene_image-414_matched.jpg", "gene-ruehlmann-88.jpg",
                       "0fbe7mpn2555j8cl7jqllel050", "playing era, #88"),
    "John Peckskamp": ("peckskamp_john_peckskamp-john-1_matched.jpg", "john-peckskamp.jpg",
                       "35sde5d1vl56n63cqqoff4tj60", "tennis polo portrait"),
    "Kari Yli-Renko": ("ylirenko_kari_yli-renko-kari-3_matched.jpg", "kari-yli-renko.jpg",
                       "qipl6vi4r17h7csac46bm4o232", "portrait"),
    "Geoff Hensley": ("hensley_geoff_hensley-geoff-copy_matched.jpg", "geoff-hensley.jpg",
                      "vdhjpdm4ct1h5eq49e9b6auu3e", "portrait"),
    "Bob Stratton": ("stratton_bob_all-americans-closeup_matched.jpg", "bob-stratton.jpg",
                     "kb5fjdc4i90br1qvg0mtvsu64l", "helmet close-up"),
    "Derrek Dickey": ("dickey_derrek_dickey-6-copy_matched.jpg", "derrek-dickey.jpg",
                      "a7kfmgenf164964jmb2il8ac7a", "jersey portrait"),
    "Al Nelson": ("nelson_al_nelson-al-3_matched.jpg", "al-nelson.jpg",
                  "j61tjuuenh6pd1rng2bcu45o35", "suit portrait, replaces the Eagles card"),
    "Cliff Goldmeyer": ("goldmeyer_cliff_goldmeyer-1-copy_matched.jpg", "cliff-goldmeyer.jpg",
                        "4h1rq5hahd2b1crjr62cjqa93g", "same photo without the handwritten note"),
    "Tony Yates": ("yates_tony_playing-portrait_matched.jpg", "tony-yates-playing.jpg",
                   "93dtqj572d4ipdcibtht23b500", "playing-era portrait"),
    "Jim Kelly Sr.": ("kelly_jim-sr_headshot_matched.jpg", "jim-kelly-sr.jpg",
                      "0769e2hmal0df42qge9t5a8v0m", "headshot"),
    "Jack Twyman": ("twyman_jack_no27-headshot_matched.jpg", "jack-twyman-27.jpg",
                    "kmdp7rifj14vr9bi0p5a1jsp5e", "#27 headshot"),
}
DROP = ("image_source_page_url", "image_source_url")
# Published names carry the Canto id so they never collide with an existing portrait in img/canto/.
PHOTOS = {n: (c, p[:-4] + "-" + cid[:8] + ".jpg", cid, w) for n, (c, p, cid, w) in PHOTOS.items()}
MINE = {p for _, p, _, _ in PHOTOS.values()}


def main():
    src = sys.argv[1]
    out_dir = os.path.join(HERE, "img", "canto")
    for name, (crop, published, _, _) in PHOTOS.items():
        if os.path.exists(os.path.join(out_dir, published)) and published not in MINE:
            raise SystemExit(f"{published} already exists; pick another name so the old image stays for rollback")
        im = Image.open(os.path.join(src, crop)).convert("RGB")
        im = im.resize((600, 800), Image.LANCZOS)
        im.save(os.path.join(out_dir, published), "JPEG", quality=86, optimize=True, progressive=True)

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
            status = "primary_image_present" if r["name"] in ADDITIONS else "replacement_image_sourced"
            r.update({"image_url": BASE_URL + PHOTOS[r["name"]][1], "image_status": status,
                      "image_source": "canto", "image_credit": "gobearcats"})
        lines[idx] = PREFIX + json.dumps(data, ensure_ascii=True, separators=(",", ":")) + ";"
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        print(f"{os.path.basename(path)}: {len(hits)} portraits")

    sources = {name: {"file": "img/canto/" + p[1], "canto_id": p[2], "photo": p[3]} for name, p in PHOTOS.items()}
    with open(os.path.join(out_dir, "photos-audit-2026-10-23.json"), "w") as f:
        json.dump(sources, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
