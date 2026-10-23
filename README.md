# gobearcats-embeds

Static assets loaded by Custom Script blocks on gobearcats.com (WMT CMS).

- `hof/uc-hof-dashboard.js` — original V2 dashboard, retained for rollback.
- `hof/uc-hof-dashboard.v3.js` — UC editorial restyle with Barlow, Futura PT Condensed and IBM Plex Mono.
- `hof/uc-hof-dashboard.v3-inline.js` — V3 with the hydration-safe mount loop; previously documented as the script pasted into page 8381.
- `hof/uc-hof-dashboard.v4-inline.js`, `v5-inline.js`, `v6-inline.js` — later inline variants.

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

No final print/banner artwork is changed by this update. The three conflicting historical induction dates remain unresolved, and 2026 portraits are not invented.
