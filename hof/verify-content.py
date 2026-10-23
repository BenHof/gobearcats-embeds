#!/usr/bin/env python3
"""Validate the reviewed HOF content in every maintained embed.

Run: python hof/verify-content.py [--baseline /path/to/old-checkout]
The optional baseline also checks that markup, CSS and runtime code did not change.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
review = json.loads((root / 'content-review-2026-10-23.json').read_text())
files = sorted(root.glob('uc-hof-dashboard*.js'))
errors = []

def check(ok, message):
    if not ok:
        errors.append(message)

def parse(path):
    text = path.read_text()
    matches = list(re.finditer(r'const DATA = (.*);\n', text))
    assert len(matches) == 1, f'{path}: expected exactly one DATA assignment'
    match = matches[0]
    return json.loads(match[1]), text[:match.start(1)] + '<DATA>' + text[match.end(1):]

check(len(files) == 7, 'expected seven maintained embeds')
classes_2026 = {'Connor Barwin', 'Loretta Blaut', 'Christy Hoffman', 'Bob Huggins',
                'Jason Kelce', 'Mike Kinnett', 'Wayne Mason'}
all_rows = []
for path in files:
    data, wrapper = parse(path)
    rows = data['inductees']
    index = {r['id']: r for r in rows}
    names = {r['name']: r for r in rows}
    prefix = path.name + ': '
    check(len(rows) == 229, prefix + 'expected 229 records')
    check(len(index) == len(rows) == len(names), prefix + 'duplicate IDs or names')
    check({r['name'] for r in rows if r['year'] == 2026} == classes_2026,
          prefix + '2026 class differs from the official seven inductees')
    check({r['name'] for r in rows if 'Field Hockey' in r['sports']} ==
          set(review['preserveFieldHockey']), prefix + 'incorrect Field Hockey members')
    check("1960-61 Men's Basketball Team" in names and
          "1962-63 Men's Basketball Team" not in names, prefix + 'wrong 2011 team')
    if "1960-61 Men's Basketball Team" in names:
        check('1962-63' not in names["1960-61 Men's Basketball Team"].get('image_url', ''),
              prefix + 'wrong-season photograph was retained')
    for update in review['updates']:
        row = index.get(update['id'], {})
        for key, value in update['changes'].items():
            check(row.get(key) == value, prefix + update['originalName'] + ': ' + key)
        for key in update['remove']:
            check(key not in row, prefix + update['originalName'] + ': remove ' + key)
    for row in rows:
        check(all(row.get(k) for k in ('id', 'name', 'last_name', 'initial', 'sports',
                                      'category', 'year', 'decade', 'bio')),
              prefix + row['name'] + ': required metadata missing')
        # An empty link is allowed only when no official GoBearcats page exists.
        check(bool(row.get('gb_url')) or row.get('gb_url_type') == 'none',
              prefix + row['name'] + ': link missing')
        check(row.get('gb_url_type') != 'search' and 'web.archive.org' not in row.get('gb_url', ''),
              prefix + row['name'] + ': placeholder link')
        check(row['sport_display'] == ', '.join(row['sports']),
              prefix + row['name'] + ': sports/display mismatch')
        check(row['decade'] == str(row['year'] // 10 * 10) + 's',
              prefix + row['name'] + ': year/decade mismatch')
    for key, field in [('sports', 'sports'), ('categories', 'category'),
                       ('decades', 'decade'), ('initials', 'initial')]:
        values = {value for row in rows for value in
                  (row[field] if isinstance(row[field], list) else [row[field]])}
        check(set(data[key]) == values and len(data[key]) == len(values),
              prefix + key + ': filter coverage or duplicate option')
    image_keys = {'image_url', 'image_source', 'image_credit', 'image_status', 'image_source_page_url'}
    for added in review['additions']:
        row = index.get(added['id'], {})
        # `wall` (v7 plaque locations) comes from hof/wall-enrich.py, not from the content review.
        check({k: v for k, v in row.items() if k not in image_keys | {'wall'}} ==
              {k: v for k, v in added.items() if k not in image_keys},
              prefix + added['name'] + ': incomplete addition')
        # A portrait is allowed only once it has been sourced from Canto or GoBearcats.
        check('image_url' not in row or (row.get('image_status') == 'primary_image_present'
                                         and row.get('image_source') in ('canto', 'gobearcats_current_article')),
              prefix + added['name'] + ': unsupported portrait')
    if args.baseline and (args.baseline / 'hof' / path.name).exists():
        before, old_wrapper = parse(args.baseline / 'hof' / path.name)
        guard = ("        // Class/search pages are not individual profiles; keep unsourced portraits empty.\n"
                 "        if (r.gb_url_type !== 'profile' || r.image_status === 'not_sourced') return null;\n")
        check(wrapper.count(guard) == 1 and wrapper.replace(guard, '', 1) == old_wrapper,
              prefix + 'change outside DATA and the reviewed profile-preview guard')
        expected = {r['id']: r for r in before['inductees']}
        for update in review['updates']:
            row = expected[update['id']]
            row.update(update['changes'])
            for key in update['remove']:
                row.pop(key, None)
        expected.update({r['id']: r for r in review['additions']})
        check(index == expected, prefix + 'unexpected record change or deletion')
    syntax = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True)
    check(syntax.returncode == 0, prefix + 'JavaScript syntax: ' + syntax.stderr.strip())
    all_rows.append(rows)

if all_rows:
    canonical = {r['id']: {k: r[k] for k in ('name', 'last_name', 'sports', 'sport_display',
                                          'category', 'year', 'bio')} for r in all_rows[-1]}
    for path, rows in zip(files, all_rows):
        actual = {r['id']: {k: r[k] for k in ('name', 'last_name', 'sports', 'sport_display',
                                           'category', 'year', 'bio')} for r in rows}
        check(actual == canonical, path.name + ': content differs across embed variants')

if errors:
    print(f'FAIL: {len(errors)} content checks failed across {len(files)} embeds')
    for error in errors[:35]:
        print(' - ' + error)
    raise SystemExit(1)
print(f'PASS: {len(files)} embeds; 229 unique records each; reviewed corrections, 2026 class, '
      'sport filters, required fields, cross-variant content and JavaScript syntax verified'
      + ('; layout and other runtime code unchanged' if args.baseline else ''))
