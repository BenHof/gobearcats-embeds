# gobearcats-embeds

Static assets loaded by Custom Script blocks on gobearcats.com (WMT CMS).

- `hof/uc-hof-dashboard.js` — original V2 dashboard, retained for rollback.
- `hof/uc-hof-dashboard.v3.js` — UC editorial restyle with Barlow, Futura PT Condensed and IBM Plex Mono.
- `hof/uc-hof-dashboard.v3-inline.js` — V3 with the hydration-safe mount loop; previously documented as the script pasted into page 8381.
- `hof/uc-hof-dashboard.v4-inline.js`, `v5-inline.js`, `v6-inline.js` — later inline variants.
- `hof/uc-hof-dashboard.v7-inline.js` — V6 content plus the wall: Inductee Directory / 3D Virtual Wall / 2D Wall Explorer tabs, a Printable Wall Map (PDF) button, and an "On the Wall" block in each inductee drawer with a Locate on 3D Wall button.
- `hof/wall/` — the public 3D wall (`wall_3d.html`), 2D wall explorer (`index.html`), plaque images, `master_wall_plaques.json` (public fields) and the printable PDF (`docs/HOF_Wall_Elevation.pdf`), served at <https://benhof.github.io/gobearcats-embeds/hof/wall/>.

## The 3D wall

The wall pages are built in the antigravity workspace `serene-pythagoras`, which also holds the wall planning work. Refresh the public copy and the dashboard's plaque locations with:

```sh
python3 hof/wall-sync.py          # copy the pages and only the assets they load into hof/wall/
python3 hof/wall-enrich.py        # write each inductee's plaque location(s) into V7's DATA
python3 hof/verify-content.py && node hof/verify-profile-loader.mjs
```

`wall-sync.py` leaves out the planning material: floor plans, the concourse photo gallery and the planning fields in the plaque data. It re-encodes production plaque PNGs as JPEGs and records the source commit and file hashes in `hof/wall/SOURCE.json`. It also adds a `postMessage` listener to the 3D page, because changing a cross-origin iframe's hash reloads the scene; V7 posts `{type: 'uc-hof:plaque', slot}` once the frame has loaded and uses `#plaque=<slot_id>` only for the first load. `wall-enrich.py` matches inductees to plaques by name, falling back to a single same-year name variant, and stops if any inductee has no plaque.

V7 reads `window.UC_HOF_WALL_BASE` when set, so a local copy can be tested before pushing.

## Current publication boundary

On October 23, 2026, the inline script on <https://gobearcats.com/hof> matched the **main-branch V6 source** at commit `d25f293f169c1f4b64d201843f67928bf244a71d`, with one leading newline. The public page contained 222 records, ending with the 2025 class. Updating this repository does **not** replace an inline copy already saved in WMT.

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
