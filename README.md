# gobearcats-embeds

Static assets loaded by Custom Script blocks on gobearcats.com (WMT CMS).

- `hof/uc-hof-dashboard.js` — original V2 dashboard, retained for rollback.
- `hof/uc-hof-dashboard.v3.js` — UC editorial restyle with Barlow, Futura PT Condensed and IBM Plex Mono.
- `hof/uc-hof-dashboard.v3-inline.js` — V3 with the hydration-safe mount loop; previously documented as the script pasted into page 8381.
- `hof/uc-hof-dashboard.v4-inline.js`, `v5-inline.js`, `v6-inline.js` — later inline variants.
- `hof/uc-hof-dashboard.v7-inline.js` — V6 content plus the 3D wall: Inductee Directory / 3D Virtual Wall tabs, and an "On the Wall" block in each inductee drawer with a Locate on 3D Wall button. On its page it removes the block's margins and unpins the site header.
- `hof/uc-hof-wall-page.inline.js` — the script on gobearcats.com/hof-wall (WMT page 9591): the 3D wall full window, with the site header, ticker and footer hidden. V7's "open in a new tab" link and the 3D page's Share Plaque button point there, so visitors never see the GitHub Pages address.
- `hof/wall/` — the public 3D wall (`wall_3d.html`), its plaque images and `master_wall_plaques.json` (public fields), served at <https://benhof.github.io/gobearcats-embeds/hof/wall/>.

## The 3D wall

The wall page is built in the antigravity workspace `serene-pythagoras`, which also holds the wall planning work. Refresh the public copy and the dashboard's plaque locations with:

```sh
python3 hof/wall-sync.py          # copy the 3D page and only the assets it loads into hof/wall/
python3 hof/wall-enrich.py        # write each inductee's plaque location(s) into V7's DATA
python3 hof/verify-content.py && node hof/verify-profile-loader.mjs
```

`wall-sync.py` publishes the fan-facing 3D page only: no floor plans, 2D planner, printable map or planning fields. It swaps the wall data's biographies for the dashboard's reviewed ones, re-encodes production plaque PNGs as JPEGs, and records the source commit and file hashes in `hof/wall/SOURCE.json`. Inside the gobearcats.com frame the page drops its own brand row, fits its toolbar, keeps the plaque in view above the details panel on phones, and gains a stairs button. It also adds a `postMessage` listener, because changing a cross-origin iframe's hash reloads the scene; V7 posts `{type: 'uc-hof:plaque', slot}` once the frame has loaded and uses `#plaque=<slot_id>` only for the first load. `wall-enrich.py` matches inductees to plaques by name, falling back to a single same-year name variant, and stops if any inductee has no plaque.

V7 reads `window.UC_HOF_WALL_BASE` when set, so a local copy can be tested before pushing.

## Current publication boundary

On October 23, 2026 (about 4:47 pm ET), page 8381 (<https://gobearcats.com/hof>) was switched to **V7** (`hof/uc-hof-dashboard.v7-inline.js`), replacing V6 at commit `d984999` that had been published at 2:14 pm. WMT page 9591 (<https://gobearcats.com/hof-wall>) was published with `hof/uc-hof-wall-page.inline.js`. Backups of each prior state are in the LLM Wiki under `outputs/HOF-3DWall/wmt/`. Updating this repository does **not** replace an inline copy already saved in WMT; the 3D wall itself (`hof/wall/`) is served from GitHub Pages and updates on push.

The reviewed content update supplies 229 records across all six variants. It changes the DATA payload, derived filter dictionaries and one profile-preview guard. The guard prevents class articles, search results and explicitly unsourced portraits from supplying an unrelated image or overriding individual metadata. HTML, CSS and all other runtime code remain unchanged. See [the correction manifest](hof/content-review-2026-10-23.json) for per-record changes and official evidence, including unresolved source conflicts.

## Validation

Requires Python 3 and Node.js. From the repository root:

```sh
python hof/verify-content.py
python hof/verify-content.py --baseline /path/to/prior-checkout
node hof/verify-profile-loader.mjs
```

The baseline option additionally verifies unchanged layout and runtime outside the reviewed preview guard, retention of every existing record ID, and absence of unrelated record changes. The validator covers the reviewed facts, unique records, official seven-member 2026 class, legitimate Field Hockey entries, filter coverage and JavaScript syntax. The loader regression exercises the actual loader in all six files and verifies that valid individual profile previews still load and cache. These checks do not independently certify every untouched biography statistic or image.

## WMT publication

1. Open the existing Hall of Fame page and identify its Custom Script block. Page 8381 is the historically documented page ID; verify the actual page and block in the editor.
2. Save an exact copy of the current block before editing. Recheck that the current script still corresponds to V6; stop and reconcile any intervening edits.
3. Replace the matching inline script with `hof/uc-hof-dashboard.v6-inline.js`, preserving the existing page, block and embed UI version.
4. Preview, then publish through WMT. Check 229 records, the 2026 class, Mary Wineberg/Annette Echikunwoke/Loretta Blaut sport labels, the two championship teams, genuine Field Hockey entries, search/filters and detail panels on desktop and mobile.
5. Confirm the public page after publication. Repository merge alone is not evidence of publication.

No final print/banner artwork is changed by this update, and 2026 portraits are not invented. UC's archived October 2006 Hall of Fame roster corroborates Joe Morrison (1978), John Pease (1980) and Sid Gillman (1981); their contradictory biography closings are corrected while the existing index years are retained.
