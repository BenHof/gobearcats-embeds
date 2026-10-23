(function () {
  'use strict';

  // gobearcats.com/hof-wall: the 3D Hall of Fame wall filling the window, with the site header,
  // schedule ticker and footer hidden. A #plaque=<slot_id> link opens on that plaque. The layer sits
  // under the site's cookie consent banner so visitors can still answer it.
  // Mount: <div id="uc-hof-wall-root"></div> in a Full Width Paragraph block on the same page.
  const ROOT_ID = 'uc-hof-wall-root';
  const WALL_ORIGIN = 'https://benhof.github.io';
  const WALL_PAGE = WALL_ORIGIN + '/gobearcats-embeds/hof/wall/wall_3d.html?full=1';
  const CSS =
    'body:has(#' + ROOT_ID + ') header.header,' +
    'body:has(#' + ROOT_ID + ') .schedule-ticker-desktop,' +
    'body:has(#' + ROOT_ID + ') .schedule-ticker-mobile,' +
    'body:has(#' + ROOT_ID + ') footer{display:none!important}' +
    'html:has(#' + ROOT_ID + '),body:has(#' + ROOT_ID + '){overflow:hidden!important}' +
    '#' + ROOT_ID + '{position:fixed;inset:0;z-index:1000;background:#0a0b0d}' +
    '#' + ROOT_ID + ' iframe{position:absolute;inset:0;width:100%;height:100%;border:0;display:block}';

  function plaqueHash() {
    return /^#(plaque|ref)=/.test(location.hash) ? location.hash : '';
  }

  function ensureMounted() {
    const root = document.getElementById(ROOT_ID);
    if (!root || root.querySelector('iframe')) return;
    if (!document.getElementById(ROOT_ID + '-css')) {
      const s = document.createElement('style');
      s.id = ROOT_ID + '-css';
      s.textContent = CSS;
      document.head.appendChild(s);
    }
    const frame = document.createElement('iframe');
    frame.title = '3D Hall of Fame wall, Lindner Center fourth-floor concourse';
    frame.allow = 'fullscreen; xr-spatial-tracking; accelerometer; gyroscope';
    frame.setAttribute('allowfullscreen', '');
    frame.referrerPolicy = 'strict-origin-when-cross-origin';
    frame.src = WALL_PAGE + plaqueHash();
    root.appendChild(frame);
  }

  // The wall reports what visitors do there (plaques opened, tour, shares); pass it to the site's Google Analytics.
  window.addEventListener('message', e => {
    const d = e.data;
    if (e.origin !== WALL_ORIGIN || !d || d.type !== 'uc-hof:event' || typeof window.gtag !== 'function') return;
    if (!/^hof3d_[a-z_]{1,32}$/.test(String(d.name))) return;
    const params = {};
    Object.entries(d.params || {}).forEach(([k, v]) => {
      if (/^[a-z_]{1,24}$/.test(k) && /^(string|number|boolean)$/.test(typeof v)) params[k] = typeof v === 'string' ? v.slice(0, 100) : v;
    });
    window.gtag('event', d.name, params);
  });

  // A new #plaque= on this page flies the loaded wall there instead of reloading it.
  window.addEventListener('hashchange', () => {
    const frame = document.querySelector('#' + ROOT_ID + ' iframe');
    const m = /^#plaque=(.+)$/.exec(location.hash);
    if (frame && m) frame.contentWindow.postMessage({ type: 'uc-hof:plaque', slot: decodeURIComponent(m[1]) }, WALL_ORIGIN);
  });

  ensureMounted();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ensureMounted);
  window.addEventListener('load', ensureMounted);
  try {
    new MutationObserver(ensureMounted).observe(document.documentElement || document.body, { childList: true, subtree: true });
  } catch (e) {}
})();
