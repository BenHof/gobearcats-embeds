#!/usr/bin/env python3
"""Copy the public 3D Hall of Fame wall into hof/wall/ for GitHub Pages.

    python3 hof/wall-sync.py [--source /path/to/serene-pythagoras]

The source workspace builds the 3D page (generate_3d_wall.py) and also holds the wall planning
work. This is the fan-facing copy that gobearcats.com/hof frames, so the script publishes only what
the 3D page loads once the planning extras are removed:

- wall_3d.html
- master_wall_plaques.json cut to public fields (no evidence, Canto ids, notes or install batches)
- every asset the edited page references: plaque atlases, crops, thumbs and production plaques
- production plaque PNGs (0.3-3 MB each) re-encoded as JPEGs at most 1600 px on the long edge,
  with the references rewritten to match

Edits to the page, each of which must apply exactly once or the run stops:

- Plaque biographies come from the dashboard's reviewed records (uc-hof-dashboard.v7-inline.js),
  matched to plaques the way hof/wall-enrich.py matches them. The wall data's own biographies for
  recent additions were long generated text.
- The floor plan dialog is emptied (the plans label telecom and electrical rooms and are never
  copied), and the links to the 2D wall planner are removed.
- "Full Bio Page" links point at hof.gobearcats.ai, because a root-relative /inductee/ link
  resolves to benhof.github.io when the page runs in an iframe.
- The page accepts {type: 'uc-hof:plaque', slot} from its parent window, so "Locate on 3D Wall"
  on gobearcats.com/hof flies to a plaque without reloading the scene.
- Inside the gobearcats.com frame the page drops its own brand row (the dashboard hero above it
  names the Hall of Fame), the toolbar fits instead of running off the right edge, phones keep the
  plaque in view above its details panel, and a stairs button drives the existing Hide stairs option
  (hiding the two atrium columns as well). Share links point at gobearcats.com/hof-wall, the full-window page.
- The lighting is calmed so the plaque sketches stay legible and the red wall stays UC red.

wall/SOURCE.json records the source commit, any uncommitted source changes and a hash of every
published file, so a later run can show what changed.
"""

import argparse
import hashlib
import importlib.util
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
PAGE = "wall_3d.html"
DATA = "master_wall_plaques.json"
ASSET_RE = re.compile(r"(?<![\w/.-])((?:web_assets|downloaded_photos|spatial_photos_jpg)/[A-Za-z0-9_./%-]+?\.(?:png|jpe?g|webp|svg|json|pdf))")
PAGE_DATA_RE = re.compile(r"\nconst D = (\{.*?\});\n", re.S)
EXCLUDE_PREFIXES = ("web_assets/floor_plans/",)
PUBLIC_SLOT_FIELDS = ["id", "ref_num", "wall", "col", "row", "name", "sport", "plaque_sport_line", "category",
                      "class_year", "inducted", "bio", "image", "thumb"]
PLAQUE_DIR = "web_assets/production_plaques/"
PLAQUE_EDGE, PLAQUE_QUALITY = 1600, 82

# Links to the 2D wall planner, which is not published.
PLANNER_LINKS = [
    ('<a class="btn studio" href="index.html" title="Browse the searchable 2D Inductee Directory &amp; Wall Map">'
     '<span class="long">Inductee </span>Directory ↗</a>', ''),
    ('    + (slotId ? `<a class="btn" style="background:#E00122;color:#fff;border-color:#E00122;font-weight:700;'
     'padding:7px 11px;text-decoration:none;border-radius:4px" href="index.html#plaque=${encodeURIComponent(slotId)}">'
     'Inductee Directory ↗</a>` : \'\')\n', ''),
    ("    { g: 'Quick Tours & Views', label: 'Browse 2D Inductee Directory', sub: 'Searchable grid & printable wall map', "
     "go: () => { location.href = 'index.html'; } }\n", ''),
]
# A hash change sent from another origin reloads the iframe, so the embedding page (gobearcats.com/hof)
# posts the plaque instead and the camera flies there in place. Only the direct parent is heard.
MESSAGE_LISTENER = ("addEventListener('message', e => { const d = e.data; "
                    "if (e.source === parent && parent !== window && d && d.type === 'uc-hof:plaque' && SLOT[d.slot]) "
                    "selectSlot(d.slot, true); });\n")
# gobearcats.com/hof-wall frames the page full window with ?full=1, so it keeps its own header there.
# The toolbar was laid out for a full browser window: it ran off the right edge between 901 and about
# 1300 px, and took three rows on a phone. Inside the gobearcats.com frame the dashboard hero already
# names the Hall of Fame, so the brand row goes; narrower windows tighten the controls and wrap below
# about 1100 px instead of clipping. On phones the details panel covers the lower half of the frame,
# so the navigation pad steps aside while it is open.
EMBED_HEAD = """<style id="gobearcats-embed">
  .band { flex-wrap:wrap; row-gap:8px; }
  .band #search-wrap { flex:1 1 150px; min-width:150px; }
  .hdr-ctl { flex-wrap:wrap; justify-content:flex-end; row-gap:6px; }
  html.embedded .band .brand { display:none; }
  html.embedded .band .hdr-ctl { margin-left:0; flex:1 1 auto; }
  .stairs-toggle svg { width:18px; height:18px; display:block; }
  .stairs-toggle.on { background:var(--red); border-color:var(--red); }
  #mapctl > .stairs-toggle { display:inline-flex; align-items:center; justify-content:center; }
  @media (max-width: 900px) { .hdr-ctl #stairs-btn { display:none; } #side[style*="block"] ~ #dock { display:none; } }
  @media (max-width: 900px) { html.embedded .band { padding:8px 10px; } html.embedded .hdr-ctl #hl-select { flex:1 1 auto; min-width:0; max-width:none; } }
  @media (max-width: 1280px) and (min-width: 901px) { .band .kicker { font-size:7.5px; letter-spacing:.08em; } .band h1 { font-size:20px; } .hdr-ctl #hl-select { max-width:192px; } .hdr-ctl #goto { max-width:150px; } }
  @media (max-width: 1180px) and (min-width: 901px) { .band #search-wrap { min-width:120px; flex-basis:120px; } .hdr-ctl #goto { max-width:128px; } #search-wrap kbd { display:none; } .hdr-ctl #tour-btn { padding:7px 9px; } }
</style>
<script>try { if (window.self !== window.top && !/[?&]full=1/.test(location.search)) document.documentElement.classList.add('embedded'); } catch (e) { document.documentElement.classList.add('embedded'); }</script>
"""
# The Hide stairs option survives in the build but its checkbox is hidden; these buttons drive it, so a
# visitor can clear the staircase that stands between the camera and much of the wall. The toolbar
# button is for desktop; phones get one in the bottom control bar, where the header has no room.
STAIRS_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><path d="M3 20h5v-5h5v-5h5V5h3"/></svg>')
STAIRS_BUTTON = ('<button id="stairs-btn" class="ico stairs-toggle" type="button" aria-pressed="false" title="Hide the stairs" '
                 'aria-label="Hide the stairs">' + STAIRS_SVG + '</button>\n      ')
STAIRS_FAB = ('<button class="stairs-toggle" type="button" aria-pressed="false" title="Hide the stairs" '
              'aria-label="Hide the stairs">' + STAIRS_SVG + '</button>')
STAIRS_ANCHOR = "cb.onchange = () => { apply(cb.checked); try { localStorage.setItem(KEY, cb.checked ? '1' : '0'); } catch (e) {} }; }"
STAIRS_JS = """
{ const btns = [...document.querySelectorAll('.stairs-toggle')], cb = document.getElementById('opt-hide-stairs');   // buttons for Hide stairs
  const cols = []; scene.traverse(o => { if (o.name === 'atriumColumn') cols.push(o); });   // the atrium columns go with the stairs
  const sync = () => { cols.forEach(o => { o.visible = !cb.checked; }); btns.forEach(b => { const off = cb.checked; b.classList.toggle('on', off); b.setAttribute('aria-pressed', off ? 'true' : 'false');
    b.title = off ? 'Show the stairs' : 'Hide the stairs'; b.setAttribute('aria-label', b.title); }); };
  btns.forEach(b => { b.onclick = () => { cb.checked = !cb.checked; cb.dispatchEvent(new Event('change')); }; });
  cb.addEventListener('change', sync); sync(); }
{ const side = document.getElementById('side'), top = document.querySelector('.top');   // phones: keep the plaque above the details panel
  const fit = () => {
    const w = innerWidth, h = innerHeight;
    if (w > 900 || side.style.display !== 'block') { if (camera.view && camera.view.enabled) { camera.clearViewOffset(); } return; }
    const above = top.getBoundingClientRect().bottom, below = side.getBoundingClientRect().top;
    camera.setViewOffset(w, h, 0, Math.max(0, h / 2 - (above + below) / 2), w, h);
  };
  new MutationObserver(fit).observe(side, { attributes: true, attributeFilter: ['style'] });
  addEventListener('resize', () => requestAnimationFrame(fit)); }"""
# Two full-height atrium columns stand where the stairs were once they are hidden; the code cites photos
# (CRW_3507, CRW_3515) that are not in the workspace, so their placement is unconfirmed. Hide them too.
COLUMN_ANCHOR = "    colMesh.receiveShadow = true;\n    atriumGroup.add(colMesh);"
COLUMN_NAMED = "    colMesh.receiveShadow = true;\n    colMesh.name = 'atriumColumn';\n    atriumGroup.add(colMesh);"
# The share button copied this page's own address; visitors should get the gobearcats.com page instead.
SHARE_URL = ("const url = `${location.origin}${location.pathname}#plaque=${encodeURIComponent(copyBtn.dataset.slot)}`;",
             "const url = `https://gobearcats.com/hof-wall#plaque=${encodeURIComponent(copyBtn.dataset.slot)}`;")
# The lighting was tuned for drama: a strong studio environment, sky and sun, and grazing spotlights
# along the top of the wall stacked up so the sketches glared out and UC red turned pink near the
# soffit. The public copy runs about a third of the spotlight and a calmer environment, and the
# plaque faces read as satin aluminium instead of clear-coated metal.
LIGHTING = [
    ("scene.environmentIntensity = 1.15;", "scene.environmentIntensity = 0.55;"),
    ("scene.add(new THREE.HemisphereLight(0xfff7f0, 0x8a6e66, 2.4));", "scene.add(new THREE.HemisphereLight(0xfff7f0, 0x8a6e66, 1.4));"),
    ("const day = new THREE.DirectionalLight(0xfff4e8, 1.6);", "const day = new THREE.DirectionalLight(0xfff4e8, 1.1);"),
    ("const s = new THREE.SpotLight(0xffe9c8, 5.2, 5.2, 0.95, 0.55, 1.2);", "const s = new THREE.SpotLight(0xffe9c8, 1.7, 5.2, 0.95, 0.55, 1.2);"),
    ("const s = new THREE.SpotLight(0xfff1dc, 6, 3.5, 0.8, 0.6, 1.3);", "const s = new THREE.SpotLight(0xfff1dc, 3, 3.5, 0.8, 0.6, 1.3);"),
    ("const troughLight = new THREE.PointLight(0xffecd0, 9, 3.8, 1.4);", "const troughLight = new THREE.PointLight(0xffecd0, 4, 3.8, 1.4);"),
    ("""const faceMat = new THREE.MeshPhysicalMaterial({
  metalness: 0.35,
  roughness: 0.38,""", """const faceMat = new THREE.MeshPhysicalMaterial({
  metalness: 0.15,
  roughness: 0.5,"""),
    ("""  clearcoat: 0.35,
  clearcoatRoughness: 0.24,
  envMapIntensity: 1.15,""", """  clearcoat: 0.12,
  clearcoatRoughness: 0.24,
  envMapIntensity: 0.6,"""),
]
SEARCH_PLACEHOLDER = ('placeholder="Find a Bearcat legend, sport, or class year…"', 'placeholder="Search inductees…"')


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


def reviewed_bios(slots):
    """{slot id: reviewed biography} from the dashboard, matched to plaques the way wall-enrich.py does."""
    spec = importlib.util.spec_from_file_location("wall_enrich", os.path.join(HERE, "wall-enrich.py"))
    enrich = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(enrich)
    _, _, data = enrich.read_dashboard(enrich.DASHBOARD)
    matched, _ = enrich.match(data["inductees"], slots)
    by_id = {r["id"]: r for r in data["inductees"]}
    return {s["id"]: by_id[rid]["bio"] for rid, hits in matched.items() for s in hits if by_id[rid].get("bio")}


def public_page(w, bios):
    m = PAGE_DATA_RE.search(w)
    if not m:
        sys.exit("wall_3d.html: const D not found.")
    d = json.loads(m.group(1))
    for s in d["slots"]:
        if s["id"] in bios:
            s["bio"] = bios[s["id"]]
    w = w[:m.start(1)] + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + w[m.end(1):]

    w = cut_div(w, '<div id="spaceplan-modal" hidden>',
                '<div id="spaceplan-modal" hidden><button class="x" id="spaceplan-close" hidden></button></div>',
                "floor plan dialog")
    for old, new in PLANNER_LINKS:
        w = replace_once(w, old, new, "2D planner link")
    if re.search(r"""['"`](index\.html|docs/)""", w):
        sys.exit("wall_3d.html still links to the 2D planner or docs/ after the edits.")
    w = replace_once(w, '<span class="hof-pill">231 Legends</span>', '', "231 Legends label")
    w = replace_once(w, *SEARCH_PLACEHOLDER, "search placeholder")
    w = replace_once(w, COLUMN_ANCHOR, COLUMN_NAMED, "atrium columns")
    w = replace_once(w, *SHARE_URL, "share link")
    for old, new in LIGHTING:
        w = replace_once(w, old, new, "lighting")
    w = replace_once(w, 'href="/inductee/${slug}"', 'href="https://hof.gobearcats.ai/inductee/${slug}"', "bio link")
    hashchange = "addEventListener('hashchange', () => { if (checkPlaqueHash()) return;"
    w = replace_once(w, hashchange, MESSAGE_LISTENER + hashchange, "plaque messages")
    w = replace_once(w, "</head>", EMBED_HEAD + "</head>", "embed styles")
    w = replace_once(w, '<button id="layers-btn"', STAIRS_BUTTON + '<button id="layers-btn"', "stairs button")
    w = replace_once(w, '<button id="layers-fab"', STAIRS_FAB + '<button id="layers-fab"', "phone stairs button")
    block = w.find("KEY = 'hof-wall-hide-stairs'")
    end = w.find(STAIRS_ANCHOR, block)
    if block < 0 or end < 0 or w.count("KEY = 'hof-wall-hide-stairs'") != 1:
        sys.exit("stairs button code: the Hide stairs block changed; update wall-sync.py.")
    end += len(STAIRS_ANCHOR)
    return w[:end] + STAIRS_JS + w[end:]


def public_data(text, bios):
    data = json.loads(text)
    slots = [{k: s[k] for k in PUBLIC_SLOT_FIELDS if k in s} for s in data["slots"]]
    for s in slots:
        if s["id"] in bios:
            s["bio"] = bios[s["id"]]
    return json.dumps({"walls": data["walls"], "slots": slots}, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    source = ap.parse_args().source

    raw_data = open(os.path.join(source, DATA), encoding="utf-8").read()
    bios = reviewed_bios(json.loads(raw_data)["slots"])
    texts = {PAGE: public_page(open(os.path.join(source, PAGE), encoding="utf-8").read(), bios),
             DATA: public_data(raw_data, bios)}
    assets = sorted({m.group(1) for t in texts.values() for m in ASSET_RE.finditer(t)})
    leaked = [a for a in assets if a.startswith(EXCLUDE_PREFIXES)]
    if leaked:
        sys.exit(f"The edited page still references excluded files: {leaked}")
    missing = [a for a in assets if not os.path.exists(os.path.join(source, a))]
    if missing:
        sys.exit(f"Referenced but missing in the source: {missing[:10]}")

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

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

    files = {}
    for root, _, names in os.walk(OUT):
        for n in sorted(names):
            path = os.path.join(root, n)
            files[os.path.relpath(path, OUT)] = {"bytes": os.path.getsize(path), "sha256": sha256(path)}
    dirty = [l[3:] for l in git(source, "status", "--porcelain").splitlines() if l[3:] in (PAGE, DATA)]
    manifest = {
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "source_branch": git(source, "rev-parse", "--abbrev-ref", "HEAD"),
        "source_commit": git(source, "rev-parse", "HEAD"),
        "source_uncommitted": dirty,
        "reviewed_bios": len(bios),
        "plaques_reencoded": f"{len(renames)} PNG to JPEG, <= {PLAQUE_EDGE} px, q{PLAQUE_QUALITY}",
        "total_bytes": sum(v["bytes"] for v in files.values()),
        "files": dict(sorted(files.items())),
    }
    with open(os.path.join(OUT, "SOURCE.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"{len(files)} files, {manifest['total_bytes'] / 1e6:.1f} MB in {OUT}; "
          f"{len(bios)} reviewed bios; re-encoded {len(renames)} plaques")
    if dirty:
        print(f"note: the source has uncommitted changes in {dirty}")


if __name__ == "__main__":
    main()
