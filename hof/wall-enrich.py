#!/usr/bin/env python3
"""Add each inductee's plaque location on the Lindner Center wall to a dashboard's DATA.

    python3 hof/wall-enrich.py [hof/uc-hof-dashboard.v7-inline.js]

Reads hof/wall/master_wall_plaques.json (written by hof/wall-sync.py) and sets `wall` on every
inductee record: a list of {slot_id, wing, section_num, column, row, plaque_num}, one entry per
plaque (Jim Holstein has two). `wing` is "main" or "panel"; `section_num` is 1 for main-wall
columns 1-15 (the red C-Paw wall) and 2 for columns 16-36 (under the HALL OF FAME letters), and 1
on the panel. `row` is the wall's own coordinate (-1 and 0 are the two upper rows); the 3D wall
labels it Row row+2. `slot_id` is the 3D wall's #plaque= deep-link id.

Names match exactly after normalising case, accents and punctuation. Otherwise the record must
match exactly one remaining plaque from the same induction year by name similarity, so a renamed
plaque ("Charlie Keating" for "Charles Keating") still matches, but two candidates never guess.
The run stops if any inductee has no plaque.
"""

import difflib
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
WALL = os.path.join(HERE, "wall", "master_wall_plaques.json")
DASHBOARD = os.path.join(HERE, "uc-hof-dashboard.v7-inline.js")
PREFIX = "  const DATA = "
MIN_SIMILARITY, MIN_MARGIN = 0.6, 0.15


def norm(name):
    n = unicodedata.normalize("NFD", name)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn").lower().replace("’", "'")
    n = re.sub(r"[^a-z0-9 ]", " ", n.replace(".", "").replace(",", ""))
    return " ".join(n.split())


def location(s):
    main = s["wall"] == "main"
    return {"slot_id": s["id"], "wing": s["wall"], "section_num": (1 if s["col"] <= 15 else 2) if main else 1,
            "column": s["col"], "row": s["row"], "plaque_num": s["ref_num"]}


def read_dashboard(path):
    """The dashboard file's lines, the index of its DATA line, and the parsed DATA."""
    lines = open(path, encoding="utf-8").read().split("\n")
    idx = next(i for i, l in enumerate(lines) if l.startswith(PREFIX))
    return lines, idx, json.loads(lines[idx][len(PREFIX):-1])


def match(inductees, slots):
    """{inductee id: [plaque slots]} plus the name-variant matches made; stops if any inductee has no plaque."""
    slots = [s for s in slots if s.get("inducted")]   # skips the dedication plaque
    by_name = {}
    for s in slots:
        by_name.setdefault(norm(s["name"]), []).append(s)
    matched, used, fuzzy = {}, set(), []
    for r in inductees:
        hits = by_name.get(norm(r["name"]))
        if hits:
            matched[r["id"]] = hits
            used.update(s["id"] for s in hits)
    for r in inductees:
        if r["id"] in matched:
            continue
        pool = [s for s in slots if s["id"] not in used and str(s["inducted"]) == str(r["year"])]
        ranked = sorted(((difflib.SequenceMatcher(None, norm(r["name"]), norm(s["name"])).ratio(), s) for s in pool),
                        key=lambda x: -x[0])
        if not ranked or ranked[0][0] < MIN_SIMILARITY or (len(ranked) > 1 and ranked[0][0] - ranked[1][0] < MIN_MARGIN):
            sys.exit(f"No unambiguous plaque for {r['name']} ({r['year']}): {[(round(a, 2), s['name']) for a, s in ranked[:3]]}")
        matched[r["id"]] = [ranked[0][1]]
        used.add(ranked[0][1]["id"])
        fuzzy.append(f"{r['name']} -> {ranked[0][1]['name']}")
    return matched, fuzzy


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else DASHBOARD
    lines, idx, data = read_dashboard(target)
    slots = json.load(open(WALL))["slots"]
    matched, fuzzy = match(data["inductees"], slots)

    for r in data["inductees"]:
        r["wall"] = [location(s) for s in sorted(matched[r["id"]], key=lambda s: s["ref_num"])]
    lines[idx] = PREFIX + json.dumps(data, ensure_ascii=True, separators=(",", ":")) + ";"
    open(target, "w", encoding="utf-8").write("\n".join(lines))

    used = {s["id"] for hits in matched.values() for s in hits}
    unplaced = [s["name"] for s in slots if s.get("inducted") and s["id"] not in used]
    print(f"{len(data['inductees'])} inductees placed on {len(used)} plaques ({len(fuzzy)} by name variant)")
    for f in fuzzy:
        print("  " + f)
    if unplaced:
        print(f"plaques with no dashboard record: {unplaced}")


if __name__ == "__main__":
    main()
