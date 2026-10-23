// Exercise the actual preview loader from every embed, without running the UI.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const root = path.dirname(fileURLToPath(import.meta.url));
for (const file of readdirSync(root).filter(n => /^uc-hof-dashboard.*\.js$/.test(n))) {
  const source = readFileSync(path.join(root, file), 'utf8');
  const match = source.match(/async function loadOfficialProfile\(r\) \{[\s\S]*?\n      \}/);
  assert.ok(match, `${file}: loader exists`);
  const requests = [];
  const preview = { image: 'verified-profile-photo.webp' };
  const context = vm.createContext({
    previewUrlFor: r => r.gb_url,
    profileCache: new Map(),
    fetch: async url => {
      requests.push(url);
      return { ok: true, text: async () => '<html>fixture</html>' };
    },
    extractOfficialProfile: () => preview,
    window: {},
  });
  const load = vm.runInContext(`(${match[0]})`, context);
  for (const type of ['class_article', 'search', 'generated']) {
    assert.equal(await load({ gb_url: 'https://gobearcats.com/class', gb_url_type: type }),
                 null, `${file}: ${type} is not an individual profile`);
  }
  assert.equal(await load({ gb_url: 'https://gobearcats.com/held',
                           gb_url_type: 'profile', image_status: 'not_sourced' }),
               null, `${file}: explicitly unsourced image stays unsourced`);
  assert.equal(requests.length, 0, `${file}: no page fetched for unsupported preview`);
  const profile = { gb_url: 'https://gobearcats.com/athlete', gb_url_type: 'profile' };
  assert.equal(await load(profile), preview, `${file}: verified profile preview still loads`);
  assert.equal(await load(profile), preview, `${file}: profile preview still caches`);
  assert.equal(requests.length, 1, `${file}: only the actual profile was fetched once`);
}
console.log('PASS: all loaders skip class/search/generated pages and unsourced images; individual profile loading/cache retained');
