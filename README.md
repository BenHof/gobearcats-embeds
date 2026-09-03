# gobearcats-embeds

Static assets loaded by Custom Script blocks on gobearcats.com (WMT CMS).

- `hof/uc-hof-dashboard.js` — James P. Kelly UC Athletics Hall of Fame dashboard, mounted into `#uc-hof-dashboard-root` on https://gobearcats.com/hof

- `hof/uc-hof-dashboard.v3.js` — 2026-09-03 restyle to the UC editorial theme (Barlow / Futura PT Condensed / IBM Plex Mono). `hof/uc-hof-dashboard.js` stays the original V2 build for rollback.

- `hof/uc-hof-dashboard.v3-inline.js` — same V3 UI with the hydration-safe mount loop; this is what is pasted inline into the Custom Script block content field on page 8381 (no hosted file needed). The hosted files above remain as rollback.
