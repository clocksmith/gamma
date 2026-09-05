"""Compare existing implementation, runtime, and historical files to pre-edit hashes."""
from pathlib import Path
import datetime
import hashlib
import json

project = Path(__file__).resolve().parents[3]
output = Path(__file__).resolve().parent
baseline = json.loads((output / 'before.json').read_text())
changed = []
counts = {}
for name, expected in baseline['files'].items():
    category = 'runtime' if name.startswith('dist/runtime/') else name.split('/')[0]
    if name in ['versions/current.json', 'versions/current-release.json']:
        category = 'mutableReleasePointers'
    counts[category] = counts.get(category, 0) + 1
    if hashlib.sha256((project / name).read_bytes()).hexdigest() != expected:
        changed.append(name)
allowed = ['dist/runtime/content-manifest.json', 'dist/runtime/simulation-copy.json',
           'versions/current-release.json', 'versions/current.json']
assert sorted(changed) == sorted(allowed), changed
old = json.loads((project / 'versions/0.14.19/game-bundle.json').read_text())
for key in ['dist/runtime/simulation-copy.json', 'dist/runtime/content-manifest.json']:
    expected = json.dumps(old['playtestKit'][key], sort_keys=True)
    expected = expected.replace('0.14.19', '0.14.20').replace('0.8.0-rc.20-test', '0.8.0-rc.21-test')
    assert expected == json.dumps(json.loads((project / key).read_text()), sort_keys=True), key
prior = json.loads((project / 'versions/0.14.19/manifest.json').read_text())
current = json.loads((project / 'versions/0.14.20/manifest.json').read_text())
for key in ['rulesetFingerprint', 'mechanicsFingerprint', 'canonicalVariant', 'contracts', 'rng']:
    assert current[key] == prior[key], key
report = {
    'capturedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'baselineCommit': baseline['sourceCommit'], 'filesChecked': len(baseline['files']),
    'categories': counts, 'changedExistingFiles': changed, 'runtimeVersionTextOnly': True,
    'rulesetFingerprint': current['rulesetFingerprint'],
    'mechanicsFingerprint': current['mechanicsFingerprint'],
    'historicalReleasesUnchanged': True, 'labAndWebByteIdentical': True,
    'engineFingerprintNote': 'Fingerprint includes tasks/content/authored.mjs; that build helper changed. Simulation and browser implementation bytes did not.'
}
(output / 'unchanged.json').write_text(json.dumps(report, indent=2) + '\n')
print(f"preservation: verified {len(baseline['files'])} existing files; runtime differences are version text only")
