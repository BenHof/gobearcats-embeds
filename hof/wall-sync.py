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
- "Full Bio Page" becomes "More on GoBearcats.com", opening the inductee's gobearcats.com page (the
  one the dashboard's profile button opens), and is left out when there is none.
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
  html.no3d .hdr-ctl, html.no3d #search-wrap, html.no3d #dock, html.no3d #mapctl, html.no3d .legend { display:none !important; }
  /* Loading screen: the wall itself, dimmed, with a title and a bar that keeps moving while the scene builds */
  #status { position:fixed; inset:0; left:0; top:0; transform:none; z-index:60; display:grid; place-items:center; padding:24px;
    background:#050506 url('../img/hof-wall-poster.jpg') center / cover no-repeat; border:0; border-radius:0; box-shadow:none;
    font:inherit; text-transform:none; letter-spacing:normal; transition:opacity .4s ease; }
  #status::before { content:''; position:absolute; inset:0; background:radial-gradient(ellipse at center, rgba(5,5,6,.82) 0%, rgba(5,5,6,.6) 55%, rgba(5,5,6,.78) 100%); }
  #status.done { opacity:0; pointer-events:none; }
  #status .ld-card { position:relative; width:min(600px, 100%); text-align:center; color:#fff; }
  #status .ld-kicker { font:600 10px/1.3 var(--f-body); letter-spacing:.16em; text-transform:uppercase; color:#c9ccd2; }
  #status .ld-title { font:900 clamp(32px, 6vw, 52px)/.86 var(--f-head); text-transform:uppercase; letter-spacing:.01em; margin:10px 0 18px; }
  #status .ld-bar { width:min(420px, 100%); margin:0 auto; height:4px; background:rgba(255,255,255,.2); border-radius:2px; overflow:hidden; }
  #status .ld-bar i { display:block; width:38%; height:100%; background:var(--red); animation:ld-slide 1.15s ease-in-out infinite; }
  @keyframes ld-slide { from { transform:translateX(-105%); } to { transform:translateX(270%); } }
  #status .ld-step { margin-top:12px; font:500 12px/1.45 var(--f-body); color:#d6d9de; }
  @media (prefers-reduced-motion: reduce) { #status .ld-bar i { animation:none; width:100%; opacity:.55; } }
  #status .no3d-btn { display:inline-block; margin-top:16px; padding:11px 16px; border-radius:4px; background:var(--red); color:#fff; font:700 12px/1 var(--f-body); letter-spacing:.08em; text-transform:uppercase; text-decoration:none; }
</style>
<script>try { if (window.self !== window.top && !/[?&]full=1/.test(location.search)) document.documentElement.classList.add('embedded'); } catch (e) { document.documentElement.classList.add('embedded'); }</script>
<script>
(function () {   // no WebGL 2, a script error or a long stall: say so and point to the directory instead of "Loading" forever
  var SITE = 'https://gobearcats.com';
  function webgl2() { try { return !!document.createElement('canvas').getContext('webgl2'); } catch (e) { return false; } }
  function fallback(reason) {
    var s = document.getElementById('status');
    if (!s || s.getAttribute('data-fallback') || s.classList.contains('done')) return;
    s.setAttribute('data-fallback', reason);
    document.documentElement.classList.add('no3d');
    s.innerHTML = '<div class="ld-card"><div class="ld-title">The 3D wall can\\u2019t load here</div>' +
      '<div class="ld-step">It needs a browser with 3D graphics (WebGL 2), such as a current Chrome, Safari, Edge or Firefox.</div>' +
      '<a class="no3d-btn" href="' + SITE + '/hof" target="_top">Browse the Inductee Directory</a></div>';
    s.querySelector('a').addEventListener('click', function (e) {   // inside the dashboard, switch its tab instead of reloading the page
      if (!document.documentElement.classList.contains('embedded')) return;
      e.preventDefault();
      parent.postMessage({ type: 'uc-hof:directory' }, SITE);
    });
    try { if (parent !== window) parent.postMessage({ type: 'uc-hof:event', name: 'hof3d_unsupported', params: { reason: reason } }, SITE); } catch (e) {}
  }
  document.addEventListener('DOMContentLoaded', function () {
    if (!webgl2()) return fallback('no_webgl2');
    window.addEventListener('error', function () { if (document.getElementById('status')) fallback('script_error'); });
    setTimeout(function () { if (document.getElementById('status')) fallback('timeout'); }, 30000);
  });
})();
</script>
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
# The stairs start hidden so the wall is in view; a visitor who shows them is remembered ('0').
STAIRS_DEFAULT = "let saved = false; try { saved = localStorage.getItem(KEY) === '1'; } catch (e) {}"
STAIRS_DEFAULT_HIDDEN = "let saved = true; try { saved = localStorage.getItem(KEY) !== '0'; } catch (e) {}"
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
  addEventListener('resize', () => requestAnimationFrame(fit)); }
{ const track = (name, params = {}) => {   // gobearcats.com forwards these to its Google Analytics
    try { if (parent !== window) parent.postMessage({ type: 'uc-hof:event', name, params }, 'https://gobearcats.com'); } catch (e) {} };
  window.ucHofTrack = track;
  let lastSlot = null;
  const replace = history.replaceState.bind(history);
  history.replaceState = (st, title, url) => {   // opening a plaque rewrites the hash to #plaque=<slot>
    replace(st, title, url);
    const m = /#plaque=([^&]+)/.exec(String(url || '')), id = m && decodeURIComponent(m[1]);
    if (id && id !== lastSlot && SLOT[id]) { lastSlot = id; track('hof3d_plaque_view', { slot: id, inductee: SLOT[id].name }); }
  };
  document.addEventListener('click', e => {
    const share = e.target.closest('#copy-3d-link');
    if (share) track('hof3d_share', { slot: share.dataset.slot });
    if (e.target.closest('#side-body a[href^="https://gobearcats.com/"]')) track('hof3d_profile_click', { slot: state.selected || '' });
    if (e.target.closest('.stairs-toggle')) setTimeout(() => track('hof3d_stairs', { hidden: document.getElementById('opt-hide-stairs').checked }), 0);
  }, true); }"""
# The planner's scenarios (restored backers, the 2026 run in today's gaps, touch-panel mock-ups) are
# still in the page and were reachable with #scn=, #opts=, #tp= links. Only #plaque= and #ref= are read.
HASH_GET = ("const hashGet = key => { const m = new RegExp('[#&]' + key + '=([^&]*)').exec(location.hash); "
            "return m ? decodeURIComponent(m[1]) : null; };")
HASH_GET_PUBLIC = ("const hashGet = key => { if (key !== 'plaque' && key !== 'ref') return null;   // public build: no planning scenarios by URL\n"
                   "  const m = new RegExp('[#&]' + key + '=([^&]*)').exec(location.hash); return m ? decodeURIComponent(m[1]) : null; };")
# The tour spent its first three stops on the elevator lobby and architecture, and its plaque stop
# misplaced Kelce and Barwin. The public tour walks the wall and stops at each Class of 2026 plaque;
# every line comes from the inductee's official announcement.
TOUR_START = "const TOUR_STOPS = ["
TOUR_OLD_MARK = "Elevator Doors & Concourse Entrance"
TOUR_JS = """const tourAt = id => {   // stand back from a plaque, level with it, so its neighbours frame it
  const s = SLOT[id], o = slotObjs[id], p = worldPos(s);
  const n = new THREE.Vector3(0, 0, 1).applyQuaternion(o.group.getWorldQuaternion(new THREE.Quaternion()));
  return { pos: p.clone().addScaledVector(n, 1.35), look: p };
};
const tourPlaque = (id, title, sub, desc) => ({ title, sub, desc, pos: () => tourAt(id).pos, look: () => tourAt(id).look, fov: 50, dur: 1.5, stay: 6500 });
const TOUR_STOPS = [
  { title: 'The Hall of Fame Wall', sub: 'Lindner Center · Fourth-Floor Concourse', fov: FOV0, dur: 1.6, stay: 7000,
    pos: () => new THREE.Vector3(OV_X, 1.7, 8.4), look: () => new THREE.Vector3(OV_X, 1.3, 0),
    desc: 'Every plaque on this wall honors a member of the James P. Kelly UC Athletics Hall of Fame, from the first class in 1976 to the 50th anniversary Class of 2026.' },
  { title: 'The C-Paw Wall', sub: 'Columns 1–15', fov: 58, dur: 1.6, stay: 6500,
    pos: () => new THREE.Vector3(colX(7.5), EYE, 2.2), look: () => new THREE.Vector3(colX(7.5), 1.65, 0),
    desc: 'The first 15 columns hang on the UC Red wall beneath the C-Paw. Four members of the Class of 2026 are here.' },
  tourPlaque('main-c01-r-1', 'Christy Hoffman', 'Class of 2026 · Women’s Soccer',
    'The program’s career leader in shutouts and goalkeeper wins, Hoffman guided UC to its first NCAA Sweet Sixteen.'),
  tourPlaque('main-c04-r5', 'Wayne Mason', 'Class of 2026 · Men’s Track and Field',
    'A 1980 First Team All-American in the 110-meter hurdles, Mason finished fifth at that year’s Olympic Trials.'),
  tourPlaque('main-c07-r0', 'Bob Huggins', 'Class of 2026 · Men’s Basketball Coach',
    'Cincinnati’s winningest coach with 399 victories, Huggins led the Bearcats to 14 NCAA Tournaments and the 1992 Final Four.'),
  tourPlaque('main-c14-r0', 'Loretta Blaut', 'Class of 2026 · Women’s Track and Field',
    'A six-time All-American high jumper, Blaut was NCAA runner-up indoors and outdoors in 2018.'),
  { title: 'Under the Hall of Fame Letters', sub: 'Columns 16–36', fov: 62, dur: 1.8, stay: 6500,
    pos: () => new THREE.Vector3(colX(22), EYE, STAND + 0.4), look: () => new THREE.Vector3(colX(23), 1.45, 0),
    desc: 'The wall continues on brushed gray beneath the HALL OF FAME lettering, where two more 2026 inductees hang.' },
  tourPlaque('main-c21-r0', 'Mike Kinnett', 'Class of 2026 · Baseball',
    'UC’s career batting average leader at .372, Kinnett hit .407 as a sophomore in 1985.'),
  tourPlaque('main-c36-r2', 'Connor Barwin', 'Class of 2026 · Football and Men’s Basketball',
    'Barwin led the BIG EAST with 11.0 sacks in 2008, then played 10 NFL seasons and earned Pro Bowl honors.'),
  { title: 'The Concourse Feature Panel', sub: '31 Plaques', fov: 54, dur: 1.6, stay: 6500,
    pos: () => panelCentre.clone().addScaledVector(panelNormal, STAND).setY(EYE), look: () => panelCentre.clone(),
    desc: 'Beside the stairs, a separate panel holds 31 more plaques, including the last member of the Class of 2026.' },
  tourPlaque('panel-c02-r5', 'Jason Kelce', 'Class of 2026 · Football',
    'A walk-on who became a two-time All-BIG EAST lineman, Kelce went on to six All-Pro selections and a Super Bowl title with the Eagles.')
];
"""
TRACK_HOOKS = [
    ("function startTour(fromIdx = 0) {",
     "function startTour(fromIdx = 0) {\n  if (window.ucHofTrack) ucHofTrack('hof3d_tour_start', { from_stop: fromIdx + 1 });"),
    ("  if (idx < 0 || idx >= TOUR_STOPS.length) { stopTour(); return; }",
     "  if (idx < 0 || idx >= TOUR_STOPS.length) { if (idx >= TOUR_STOPS.length && window.ucHofTrack) ucHofTrack('hof3d_tour_complete'); stopTour(); return; }"),
    ("document.getElementById('status').remove();",
     "{ const st = document.getElementById('status'); st.classList.add('done'); setTimeout(() => st.remove(), 450); }\nif (window.ucHofTrack) ucHofTrack('hof3d_loaded', { mode: document.documentElement.classList.contains('embedded') ? 'dashboard' : 'full_page' });"),
]
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
# "Full Bio Page" pointed at a /inductee/ route of another site. It now opens the inductee's own
# gobearcats.com page, the one the dashboard's profile button opens, and is left out when there is none.
BIO_LINK = ("    + `<a class=\"btn\" style=\"color:#333;border-color:#d4d4d8;background:#fff;padding:7px 11px;text-decoration:none;"
            "border-radius:4px\" href=\"/inductee/${slug}\" target=\"_blank\" rel=\"noopener\">Full Bio Page ↗</a>`")
PROFILE_LINK = ("    + (PROFILE[slotId] ? `<a class=\"btn\" style=\"color:#333;border-color:#d4d4d8;background:#fff;padding:7px 11px;"
                "text-decoration:none;border-radius:4px\" href=\"${esc(PROFILE[slotId])}\" target=\"_blank\" rel=\"noopener\">"
                "More on GoBearcats.com ↗</a>` : '')")
# A second, gray C-Paw supergraphic sat just past column 35, out on the glass beyond the wall's edge,
# where there is no graphic in the building. The dark red one on the red section stays.
GLASS_CPAW = "placeCpaw(1.9, 0x3d4249, colX(35) + PW / 2 + 0.62, 1.2);\n"
# The loading card (title plus "Loading 3D Concourse") sat small in the middle of a black page with the
# toolbar and controls already showing, and the dashboard added its own text on top. One loading screen
# now covers the page until the scene is ready, then fades.
STATUS_OLD = ('<div id="status">James P. Kelly University of Cincinnati Athletics Hall of Fame'
              '<small>Loading 3D Concourse · Lindner Center Level 4</small></div>')
STATUS_NEW = ('<div id="status" role="status" aria-live="polite"><div class="ld-card">'
              '<div class="ld-kicker">James P. Kelly UC Athletics Hall of Fame</div>'
              '<div class="ld-title">The Hall of Fame Wall</div><div class="ld-bar"><i></i></div>'
              '<div class="ld-step">Setting up the Lindner Center concourse and all 231 plaques…</div></div></div>')
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


def dashboard_records(slots):
    """{slot id: dashboard inductee record}, matched to plaques the way wall-enrich.py does."""
    spec = importlib.util.spec_from_file_location("wall_enrich", os.path.join(HERE, "wall-enrich.py"))
    enrich = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(enrich)
    _, _, data = enrich.read_dashboard(enrich.DASHBOARD)
    matched, _ = enrich.match(data["inductees"], slots)
    by_id = {r["id"]: r for r in data["inductees"]}
    return {s["id"]: by_id[rid] for rid, hits in matched.items() for s in hits}


def reviewed_bios(records):
    return {sid: r["bio"] for sid, r in records.items() if r.get("bio")}


def profile_urls(records):
    """{slot id: the inductee's gobearcats.com page}, the same page the dashboard's profile button opens."""
    out = {}
    for sid, r in records.items():
        url = r.get("current_gb_url") or r.get("gb_url")
        kind = r.get("current_gb_url_type") or r.get("gb_url_type")
        if url and url.startswith("https://gobearcats.com/") and kind in ("profile", "class_article", "article"):
            out[sid] = url
    return out


def public_page(w, bios, profiles):
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
    w = replace_once(w, STATUS_OLD, STATUS_NEW, "loading screen")
    w = replace_once(w, COLUMN_ANCHOR, COLUMN_NAMED, "atrium columns")
    w = replace_once(w, GLASS_CPAW, "", "gray C-Paw past the wall")
    w = replace_once(w, *SHARE_URL, "share link")
    for old, new in LIGHTING:
        w = replace_once(w, old, new, "lighting")
    w = replace_once(w, HASH_GET, HASH_GET_PUBLIC, "planning links")
    start = w.find(TOUR_START)
    end = w.find("\n];\n", start)
    if start < 0 or end < 0 or w.count(TOUR_START) != 1 or TOUR_OLD_MARK not in w[start:end]:
        sys.exit("guided tour: the TOUR_STOPS block changed; update wall-sync.py.")
    w = w[:start] + TOUR_JS + w[end + len("\n];\n"):]
    for old, new in TRACK_HOOKS:
        w = replace_once(w, old, new, "analytics hooks")
    w = replace_once(w, BIO_LINK, PROFILE_LINK, "bio link")
    w = replace_once(w, "function profileLinks(name, sport, yr, slotId) {",
                     "const PROFILE = " + json.dumps(profiles, sort_keys=True) + ";\nfunction profileLinks(name, sport, yr, slotId) {",
                     "profile urls")
    hashchange = "addEventListener('hashchange', () => { if (checkPlaqueHash()) return;"
    w = replace_once(w, hashchange, MESSAGE_LISTENER + hashchange, "plaque messages")
    w = replace_once(w, "</head>", EMBED_HEAD + "</head>", "embed styles")
    w = replace_once(w, '<button id="layers-btn"', STAIRS_BUTTON + '<button id="layers-btn"', "stairs button")
    w = replace_once(w, '<button id="layers-fab"', STAIRS_FAB + '<button id="layers-fab"', "phone stairs button")
    block = w.find("KEY = 'hof-wall-hide-stairs'")
    default = w.find(STAIRS_DEFAULT, block)
    if block < 0 or default < 0 or default > w.find(STAIRS_ANCHOR, block):
        sys.exit("stairs default: the Hide stairs block changed; update wall-sync.py.")
    w = w[:default] + STAIRS_DEFAULT_HIDDEN + w[default + len(STAIRS_DEFAULT):]
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
    records = dashboard_records(json.loads(raw_data)["slots"])
    bios, profiles = reviewed_bios(records), profile_urls(records)
    texts = {PAGE: public_page(open(os.path.join(source, PAGE), encoding="utf-8").read(), bios, profiles),
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
