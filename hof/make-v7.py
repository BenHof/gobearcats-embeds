"""Derive hof/uc-hof-dashboard.v7-inline.js from v6: Directory / 3D Virtual Wall tabs, the 3D wall frame
(preloaded, full width), the wall location in the drawer, page CSS for gobearcats.com/hof and GA4 events.

    python3 hof/make-v7.py && python3 hof/wall-enrich.py

V6 already carries the reviewed bios and replacement photos, so rebuild V7 from it after any V6 change,
then run wall-enrich.py to add each inductee's wall location."""
import json
import sys

import os
REPO = os.path.dirname(os.path.abspath(__file__)) + '/'
src = open(REPO + 'uc-hof-dashboard.v6-inline.js').read().split('\n')
assert src[5].startswith('  const DATA = ') and src[6].startswith('  const CSS = ') and src[7].startswith('  const HTML = ')
css = json.loads(src[6][len('  const CSS = '):-1])
html = json.loads(src[7][len('  const HTML = '):-1])
code = '\n'.join(src[8:])


def sub(text, old, new, label):
    if text.count(old) != 1:
        sys.exit(f'{label}: {text.count(old)} matches')
    return text.replace(old, new)


# ---------- HTML ----------
html = sub(html, '''      <p class="lede">Search the official Cincinnati Athletics Hall of Fame index by inductee, sport, role, class year, or category. <b>Open any record for a quick preview</b>, then jump to the full GoBearcats profile page.</p>
    </div>
  </div>
</section>
''', '''      <p class="lede">Search the official Cincinnati Athletics Hall of Fame index by inductee, sport, role, class year, or category. <b>Open any record for a quick preview</b>, then jump to the full GoBearcats profile page.</p>
    </div>
  </div>

  <div class="view-bar">
    <div class="view-tabs" id="viewTabs" role="tablist" aria-label="Hall of Fame views">
      <button class="view-tab active" type="button" role="tab" id="tab-directory" data-view-tab="directory" aria-controls="view-directory" aria-selected="true"><span class="t-long">Inductee </span>Directory</button>
      <button class="view-tab" type="button" role="tab" id="tab-3d" data-view-tab="3d" aria-controls="view-3d" aria-selected="false" tabindex="-1">3D <span class="t-long">Virtual </span>Wall</button>
    </div>
  </div>
</section>

<div class="view" id="view-directory" role="tabpanel" aria-labelledby="tab-directory" data-view="directory">
''', 'hero')

html = sub(html, '''  </section>
</main>
''', '''  </section>
</main>
</div>

<div class="view" id="view-3d" role="tabpanel" aria-labelledby="tab-3d" data-view="3d" hidden>
  <section class="wall-stage" aria-label="3D Hall of Fame wall">
    <div class="frame-wrap" id="frameWrap3d">
      <iframe id="frame3d" title="3D Hall of Fame wall, Lindner Center fourth-floor concourse" allow="fullscreen; xr-spatial-tracking; accelerometer; gyroscope" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
    </div>
    <a class="stage-link" id="open3d" href="#" target="_blank" rel="noopener">Open the 3D wall in a new tab ↗</a>
  </section>
</div>
''', 'views')

html = sub(html, '''    <div class="field">
      <h4>Biography</h4>''', '''    <div class="field wall-loc" id="dWall" hidden>
      <h4>On the Wall</h4>
      <div class="wall-spots" id="dWallSpots"></div>
    </div>

    <div class="field">
      <h4>Biography</h4>''', 'drawer')

# ---------- CSS ----------
css = sub(css, '''.hof-hero {
  background: #000;
  color: #fff;
  border-bottom: 5px solid var(--red);
  padding: 40px 0 34px;''', '''.hof-hero {
  background: #000;
  color: #fff;
  border-bottom: 5px solid var(--red);
  padding: 40px 0 0;''', 'hero padding')

css += '''
/* Views: directory and 3D wall */
[hidden] {
  display: none !important;
}

.view-bar {
  max-width: 1440px;
  margin: 30px auto 0;
  padding: 0 26px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.view-tabs {
  display: flex;
  gap: 2px;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: none;
}

.view-tabs::-webkit-scrollbar {
  display: none;
}

.view-tab {
  appearance: none;
  border: 0;
  border-radius: 7px 7px 0 0;
  background: transparent;
  color: rgba(255,255,255,.66);
  padding: 15px 18px 13px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: .1em;
  text-transform: uppercase;
  white-space: nowrap;
  cursor: pointer;
  transition: background .12s ease, color .12s ease;
}

.view-tab:hover {
  color: #fff;
  background: rgba(255,255,255,.09);
}

.view-tab.active {
  color: #fff;
  background: var(--red);
}

.view-tab:focus-visible {
  outline: 2px solid #fff;
  outline-offset: -2px;
}

.hof-hero {
  margin-bottom: 0;
}

#view-directory {
  padding-top: 26px;
}

/* The 3D wall runs edge to edge under the tabs, like part of the page rather than a framed window. */
.wall-stage {
  padding: 0 0 28px;
}

.frame-wrap {
  position: relative;
  height: max(480px, calc(100vh - 46px));
  height: max(480px, calc(100svh - 46px));
  overflow: hidden;
  background: #050506;
}

/* Loading ahead of a click: laid out at full size but off screen, so the scene is built when it is shown. */
.view.preloading {
  display: block !important;
  position: absolute;
  left: -200vw;
  top: 0;
  width: 100%;
  visibility: hidden;
  pointer-events: none;
}

.frame-wrap iframe {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}

.stage-link {
  display: block;
  width: fit-content;
  margin: 10px 26px 0 auto;
  color: var(--muted);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}

.stage-link:hover {
  color: var(--red);
}

/* Drawer: where the plaque hangs */
.wall-loc {
  padding: 14px 16px;
  border: 1px solid var(--rule);
  border-left: 4px solid var(--red);
  border-radius: 7px;
}

.wall-spot + .wall-spot {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--rule-soft);
}

.wall-place {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 10px;
  margin: 0 0 10px;
  color: var(--ink);
  font-weight: 600;
  line-height: 1.4;
}

.wall-place .mono {
  color: var(--red);
  font-size: 12.5px;
  font-weight: 600;
}

.wall-cta {
  appearance: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  border-radius: 7px;
  background: var(--ink);
  color: #fff;
  padding: 10px 14px;
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background .12s ease;
}

.wall-cta:hover {
  background: var(--red);
}

.wall-cta:focus-visible,
.stage-link:focus-visible {
  outline: 2px solid var(--red);
  outline-offset: 2px;
}

@media (max-width: 700px) {
  .hof-hero {
    padding-bottom: 0;
  }

  .view-bar {
    margin-top: 22px;
    padding: 0 18px;
  }

  .view-tab {
    padding: 14px 13px 12px;
    font-size: 12px;
  }

  #view-directory {
    padding-top: 18px;
  }

  .wall-stage {
    padding: 0 0 28px;
  }

  .frame-wrap {
    height: max(420px, calc(100svh - 44px));
  }

  .stage-link {
    margin-right: 18px;
  }
}

@media (max-width: 520px) {
  .view-tab .t-long {
    display: none;
  }
}
'''

# On this page only: the Full Width Paragraph block that holds the mount adds 85 px above and below and
# 17 px side gutters, so the dashboard runs edge to edge instead; the site header scrolls away with the
# page rather than staying pinned over the 3D wall; and the schedule ticker and footer sponsors are hidden.
PAGE_CSS = (".full-width-paragraph:has(#uc-hof-dashboard-root){margin:0!important}"
            ".full-width-paragraph__container:has(#uc-hof-dashboard-root){padding:0!important;max-width:none!important}"
            "body:has(#uc-hof-dashboard-root) header.header{position:relative!important;top:auto!important}"
            "body:has(#uc-hof-dashboard-root) .schedule-ticker-desktop{display:none!important}"
            "body:has(#uc-hof-dashboard-root) footer > .content-blocks--default:has(> .sponsors){display:none!important}")

# ---------- code ----------
code = sub(code, '''  function init() {
    const host = findHost();''', '''  function pageCss() {
    if (document.getElementById('uc-hof-page-css')) return;
    const s = document.createElement('style');
    s.id = 'uc-hof-page-css';
    [['https://benhof.github.io', ''], ['https://cdn.jsdelivr.net', 'anonymous']].forEach(([href, cors]) => {
      const l = document.createElement('link');
      l.rel = 'preconnect'; l.href = href; if (cors) l.crossOrigin = cors;
      document.head.appendChild(l);
    });
    s.textContent = ''' + json.dumps(PAGE_CSS) + ''';
    document.head.appendChild(s);
  }

  function init() {
    pageCss();
    const host = findHost();''', 'page css')

code = sub(code, '''      function filteredSorted() {
        return records
          .filter(recordMatches)
          .sort((a,b) => {
            const av = sortValue(a, state.sortKey);''', '''      // While searching, inductees whose name matches come before those matched by sport or biography.
      function nameRank(r) {
        return state.q && !String(r.name || '').toLowerCase().includes(state.q) ? 1 : 0;
      }

      function filteredSorted() {
        return records
          .filter(recordMatches)
          .sort((a,b) => {
            const rank = nameRank(a) - nameRank(b);
            if (rank) return rank;
            const av = sortValue(a, state.sortKey);''', 'search rank')

code = sub(code, '''      const drawer = root.getElementById('drawer');
      const overlay = root.getElementById('overlay');
      let activeDrawerId = null;
''', '''      const drawer = root.getElementById('drawer');
      const overlay = root.getElementById('overlay');
      let activeDrawerId = null;

      // The 3D wall lives on GitHub Pages and loads in an iframe on first view; "new tab" opens
      // gobearcats.com/hof-wall, which frames the same page full window.
      const WALL_BASE = String(window.UC_HOF_WALL_BASE || 'https://benhof.github.io/gobearcats-embeds/hof/wall/').replace(/\\/?$/, '/');
      const WALL_PAGE = WALL_BASE + 'wall_3d.html';
      const FULL_PAGE = 'https://gobearcats.com/hof-wall';
      const viewTabs = Array.from(root.querySelectorAll('[data-view-tab]'));
      const viewPanels = Array.from(root.querySelectorAll('[data-view]'));
      const frame3d = root.getElementById('frame3d');
      let wallLoaded = false;

      root.getElementById('open3d').href = FULL_PAGE;

      frame3d.addEventListener('load', () => { wallLoaded = true; });

      // Start the 3D wall before it is asked for: on desktop once the page settles, and anywhere at the
      // first sign of intent (pointing at or touching the tab, opening an inductee), so it is ready sooner.
      function preloadWall() {
        if (frame3d.getAttribute('src')) return;
        const panel = root.getElementById('view-3d');
        if (panel.hidden) panel.classList.add('preloading');
        frame3d.src = WALL_PAGE;
      }
      const tab3d = root.getElementById('tab-3d');
      ['pointerenter', 'focus'].forEach(ev => tab3d.addEventListener(ev, preloadWall));
      tab3d.addEventListener('touchstart', preloadWall, { passive: true });
      if (window.matchMedia && matchMedia('(pointer: fine)').matches && window.innerWidth >= 1024) {
        const later = () => setTimeout(preloadWall, 1200);
        if (document.readyState === 'complete') later(); else window.addEventListener('load', later, { once: true });
      }

      // Bring the tabs to the top of the window (under the site header if it is pinned), so the whole 3D frame is in view.
      function scrollToTabs() {
        const header = document.querySelector('header.header');
        const offset = header && /sticky|fixed/.test(getComputedStyle(header).position) ? header.offsetHeight : 0;
        const y = root.getElementById('viewTabs').parentElement.getBoundingClientRect().top + window.scrollY - offset;
        if (Math.abs(y - window.scrollY) < 4) return;
        const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
      }

      function showView(name, focusTab) {
        viewPanels.forEach(p => { p.hidden = p.dataset.view !== name; p.classList.remove('preloading'); });
        viewTabs.forEach(t => {
          const on = t.dataset.viewTab === name;
          t.classList.toggle('active', on);
          t.setAttribute('aria-selected', on ? 'true' : 'false');
          t.tabIndex = on ? 0 : -1;
          if (on && focusTab) t.focus();
        });
        if (name === '3d' && !frame3d.getAttribute('src')) frame3d.src = WALL_PAGE;
      }

      // Visitors' use of the tabs and the 3D wall goes to the site's Google Analytics (gtag).
      function track(name, params) {
        if (!/^hof(3d)?_[a-z_]{1,32}$/.test(String(name)) || typeof window.gtag !== 'function') return;
        const clean = {};
        Object.entries(params || {}).forEach(([k, v]) => {
          if (/^[a-z_]{1,24}$/.test(k) && /^(string|number|boolean)$/.test(typeof v)) clean[k] = typeof v === 'string' ? v.slice(0, 100) : v;
        });
        window.gtag('event', name, clean);
      }

      // The 3D page reports events and, when it cannot run, asks for the directory instead.
      if (window.__ucHofOnMessage) window.removeEventListener('message', window.__ucHofOnMessage);
      window.__ucHofOnMessage = e => {
        if (e.origin !== new URL(WALL_BASE).origin || !e.data) return;
        if (e.data.type === 'uc-hof:event') {   // a load in the background is not a visit to the 3D tab
          const params = Object.assign({}, e.data.params);
          if (e.data.name === 'hof3d_loaded') params.shown = !root.getElementById('view-3d').hidden;
          track(e.data.name, params);
        }
        if (e.data.type === 'uc-hof:directory') { showView('directory'); scrollToTabs(); }
      };
      window.addEventListener('message', window.__ucHofOnMessage);

      viewTabs.forEach((t, i) => {
        t.addEventListener('click', () => { showView(t.dataset.viewTab); scrollToTabs(); track('hof_tab_view', { tab: t.dataset.viewTab }); });
        t.addEventListener('keydown', e => {
          const step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
          if (!step) return;
          e.preventDefault();
          showView(viewTabs[(i + step + viewTabs.length) % viewTabs.length].dataset.viewTab, true);
        });
      });

      // Same wording as the 3D wall's own plaque panel, which counts rows from the top (row -1 is Row 1).
      function wallPlace(w) {
        return (w.wing === 'panel' ? 'Concourse Feature Panel' : 'Main Wall') + ' · Column ' + w.column + ', Row ' + (Number(w.row) + 2);
      }

      // Once the 3D page has loaded, ask it to fly to the plaque: changing a cross-origin iframe's
      // hash reloads the whole scene. The first visit loads straight to the plaque.
      function locateOnWall(slotId) {
        const hash = '#plaque=' + encodeURIComponent(slotId);
        const r = records.find(x => x.id === activeDrawerId);
        track('hof_locate', { slot: slotId, inductee: r ? r.name : '' });
        closeDrawer();
        if (wallLoaded && frame3d.contentWindow) {
          frame3d.contentWindow.postMessage({ type: 'uc-hof:plaque', slot: slotId }, new URL(WALL_BASE).origin);
        } else {
          frame3d.src = WALL_PAGE + hash;
        }
        root.getElementById('open3d').href = FULL_PAGE + hash;
        showView('3d');
        requestAnimationFrame(scrollToTabs);
      }

      root.getElementById('dWallSpots').addEventListener('click', e => {
        const b = e.target.closest('[data-slot]');
        if (b) locateOnWall(b.dataset.slot);
      });
''', 'wall views code')

code = sub(code, '''        const snapshot = makeSnapshot(r.bio);''', '''        const spots = Array.isArray(r.wall) ? r.wall : [];
        if (spots.length) preloadWall();
        root.getElementById('dWall').hidden = !spots.length;
        root.getElementById('dWallSpots').innerHTML = spots.map(w =>
          '<div class="wall-spot"><p class="wall-place"><span>' + escapeHtml(wallPlace(w)) + '</span><span class="mono">Plaque #' + escapeHtml(w.plaque_num) + '</span></p>' +
          '<button class="wall-cta" type="button" data-slot="' + escapeAttr(w.slot_id) + '">' + (spots.length > 1 ? 'Locate Plaque #' + escapeHtml(w.plaque_num) : 'Locate on 3D Wall') + ' →</button></div>'
        ).join('');

        const snapshot = makeSnapshot(r.bio);''', 'drawer populate')

out = '\n'.join(src[:6] + ['  const CSS = ' + json.dumps(css) + ';', '  const HTML = ' + json.dumps(html) + ';', code])
open(REPO + 'uc-hof-dashboard.v7-inline.js', 'w').write(out)
print('wrote v7', len(out))
