"""Native-ABI / pure-core regression checker for the 66-problem development cohorts.

Scope (honest): a regression gate over declared contracts, not a proof of purity
and not catalogue qualification. Qualification stays unknown. It checks:

1. Export shape: every cohort JavaScript module loads in a fresh `node --jitless`
   process and exposes a callable `solve` (callable module or `.solve`) and its
   official entry (named export, `Solution.prototype` method or native class);
   every Python module exposes `solve` and `Solution.<name>` or a native class.
   The qualified 875.js object-footer module must load through run-case.cjs with
   its qualified hash unchanged.
2. Representation-specific effects, driven by semantics fields:
   - `solve_effects` {inputMutation, outputAliasing: forbidden} on a TreeNode
     problem: native node inputs are left structurally and identically intact,
     and no output node is an input node; a cyclic input is rejected.
   - `native_effects.mutates_inputs` on a TreeNode problem: the native entry's
     result matches the expected level order.
   - `official_interface.in_place_arg` k: solve leaves args unchanged and returns
     the expected value; the native entry leaves args[k] equal to the expected
     value and every other argument unchanged.
3. `string_unit = unicode_codepoint`: the case set contains non-BMP rows and both
   languages return the oracle value on them.
4. Hash-supersession lineage: manifest files, source_inventory, semantics
   `source_sha256`, SHA256SUMS and authoring-catalog.json agree with the bytes on
   disk; every `supersedes` entry names different, retrievable bytes (history blob
   or Git) whose hash matches; and pre-source freeze amendments form unbroken
   old -> new chains ending at the current bytes.

Run: python3 check_native_abi.py   (exit 1 on any failure; JSON report on stdout)
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
AUTHORED = ROOT / 'projects/algorithm_solver/catalogue/authored'
COHORTS = ('requested-243-370-35-20261028-v1', 'requested-156-1940-31-20261028-v1')
QUALIFIED_875 = ROOT / 'projects/algorithm_solver/catalogue/authored/leetcode-eight-v1/javascript/875.js'
QUALIFIED_SUMMARY = ROOT / 'projects/algorithm_solver/catalogue/public-domain-qualification-v3/QUALIFICATION-SUMMARY-v1.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def node(script, payload):
    proc = subprocess.run(['node', '--jitless', '-e', script], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=60)
    if proc.returncode:
        raise RuntimeError(proc.stderr[-800:])
    return json.loads(proc.stdout)


JS_SHAPE = r"""
const job = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = {};
for (const [key, path, official] of job) {
  try {
    const m = require(path);
    const solve = typeof m?.solve === 'function' ? m.solve : m;
    const S = m && m.Solution;
    out[key] = {loaded: true, solve: typeof solve === 'function',
      official: official === null || typeof m[official] === 'function' ||
        (typeof S === 'function' && typeof S.prototype[official] === 'function')};
  } catch (e) { out[key] = {loaded: false, error: String(e).slice(0, 300)}; }
}
process.stdout.write(JSON.stringify(out));
"""

JS_TREE = r"""
const job = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const m = require(job.path);
const T = m.TreeNode;
function build(a) {
  if (!a.length || a[0] === null) return null;
  const n = a.map(v => v === null ? null : new T(v)); let i = 1;
  for (const x of n) { if (x === null) continue; if (i < n.length) x.left = n[i++]; if (i < n.length) x.right = n[i++]; }
  return n[0];
}
function level(r) {
  const out = [], q = [r];
  for (let i = 0; i < q.length; i++) { const x = q[i]; if (x == null) out.push(null); else { out.push(x.val); q.push(x.left, x.right); } }
  while (out.length && out[out.length - 1] === null) out.pop(); return out;
}
function nodes(r) { const s = new Map(), st = r ? [r] : []; while (st.length) { const x = st.pop(); if (s.has(x) || s.size > 100000) continue; s.set(x, [x.val, x.left, x.right]); if (x.left) st.push(x.left); if (x.right) st.push(x.right); } return s; }
const res = [];
for (const c of job.cases) {
  const root = build(c.args[0]); const before = nodes(root);
  const out = m.solve(root);
  const intact = [...before].every(([x, [v, l, r]]) => x.val === v && x.left === l && x.right === r);
  const aliased = [...nodes(out).keys()].filter(x => before.has(x)).length;
  const nroot = build(c.args[0]); const nout = m[job.official](nroot);
  res.push({solve: level(out), intact, aliased, native: level(nout)});
}
let cycle;
try { const a = new T(1); a.left = new T(2); a.left.left = a; m.solve(a); cycle = 'accepted'; }
catch (e) { cycle = 'rejected'; }
process.stdout.write(JSON.stringify({res, cycle}));
"""

JS_CALLS = r"""
const job = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const m = require(job.path);
const solve = typeof m?.solve === 'function' ? m.solve : m;
const res = [];
for (const args of job.cases) {
  const a = JSON.parse(JSON.stringify(args)); const value = solve(...a);
  const b = JSON.parse(JSON.stringify(args)); let nret = null;
  if (job.official) { const r = m[job.official](...b); nret = r === undefined ? null : r; }
  res.push({value: value === undefined ? null : value, after: a, nativeAfter: b, nativeReturn: nret});
}
process.stdout.write(JSON.stringify(res));
"""


class Report:
    def __init__(self):
        self.checks, self.failures = 0, []

    def expect(self, ok, where, what):
        self.checks += 1
        if not ok:
            self.failures.append({'where': where, 'failed': what})


def contract_rows(base):
    return {int(p['id']): p for p in json.loads((base / 'contracts.json').read_text())['problems']}


def check_shape(report, base, contracts):
    job = [[f'{pid}', str(base / 'javascript' / f'{pid}.js'), c['official_interface'].get('name')]
           for pid, c in sorted(contracts.items())]
    job.append(['875', str(QUALIFIED_875), 'minEatingSpeed'])
    got = node(JS_SHAPE, job)
    for key, _, _ in job:
        g = got[key]
        report.expect(g.get('loaded') and g.get('solve') and g.get('official'), f'{base.name}:js:{key}',
                      'module loads and exports solve plus its official entry: ' + json.dumps(g))
    for pid, c in sorted(contracts.items()):
        name = c['official_interface'].get('name')
        try:
            m = load_module(f'abi_{base.name}_{pid}'.replace('-', '_'), base / 'python' / f'{pid}.py')
            ok = callable(getattr(m, 'solve', None)) and (
                name is None or isinstance(getattr(m, name, None), type) or
                callable(getattr(getattr(m, 'Solution', None), name, None)))
        except Exception as error:  # a load failure is a shape failure
            ok = False
            name = f'{name} ({error!r})'
        report.expect(ok, f'{base.name}:py:{pid}', f'module exposes solve and official entry {name}')


def check_875(report):
    digest = sha(QUALIFIED_875.read_bytes())
    summary = json.loads(QUALIFIED_SUMMARY.read_text())
    pinned = {r['source_sha256'] for r in summary['source_outcomes'] if r['id'] == 875 and r['language'] == 'javascript'}
    report.expect(digest in pinned, 'qualified:875.js', 'source bytes still match the qualified hash')
    proc = subprocess.run(['node', '--jitless', str(HERE / 'run-case.cjs'), str(QUALIFIED_875)],
                          input=json.dumps([[3, 6, 7, 11], 8]), capture_output=True, text=True, timeout=10)
    response = json.loads(proc.stdout) if proc.returncode == 0 else {}
    report.expect(response.get('exception') is None and response.get('result') == 4 and
                  response.get('sourceSha256') == digest,
                  'qualified:875.js', 'object-footer module loads and solves through run-case.cjs')


def py_tree_checks(report, where, module, official, rows):
    T = module.TreeNode

    def build(a):
        if not a or a[0] is None:
            return None
        n = [None if v is None else T(v) for v in a]
        kids = n[::-1]
        head = kids.pop()
        for x in n:
            if x is not None:
                if kids:
                    x.left = kids.pop()
                if kids:
                    x.right = kids.pop()
        return head

    def nodes(r):
        seen, stack = {}, [r] if r is not None else []
        while stack:
            x = stack.pop()
            if id(x) in seen:
                continue
            seen[id(x)] = (x, x.val, x.left, x.right)
            stack.extend(c for c in (x.left, x.right) if c is not None)
        return seen

    for i, row in enumerate(rows):
        root = build(row['args'][0])
        before = nodes(root)
        out = module.solve(root)
        intact = all(x.val == v and x.left is l and x.right is r for x, v, l, r in before.values())
        aliased = sum(1 for k in nodes(out) if k in before)
        report.expect(intact, f'{where}:case{i}', 'solve leaves native TreeNode input intact (inputMutation forbidden)')
        report.expect(aliased == 0, f'{where}:case{i}', f'solve output shares no input node (outputAliasing forbidden); shared={aliased}')
        report.expect(module._to_level(out) == row['expected'], f'{where}:case{i}', 'solve result on native input')
        nout = getattr(module.Solution(), official)(build(row['args'][0]))
        report.expect(module._to_level(nout) == row['expected'], f'{where}:case{i}', 'native entry result')
    a = T(1)
    a.left = T(2)
    a.left.left = a
    try:
        module.solve(a)
        rejected = False
    except ValueError:
        rejected = True
    report.expect(rejected, f'{where}:cycle', 'solve rejects a cyclic node graph')


def check_effects(report, base, contracts, cases):
    for pid in sorted(contracts):
        official = contracts[pid]['official_interface']
        for language, ext in (('python', 'py'), ('javascript', 'js')):
            sem = json.loads((base / 'semantics' / f'{pid}-{language}.json').read_text())
            where = f'{base.name}:{language}:{pid}'
            in_place = sem['official_interface'].get('in_place_arg')
            report.expect(in_place == official.get('in_place_arg'), where,
                          'semantics and contracts agree on official_interface.in_place_arg')
            native = sem.get('native_effects')
            if in_place is not None:
                report.expect(bool(native and native.get('mutates_inputs') and native.get('in_place_arg') == in_place),
                              where, 'in_place_arg is declared as native_effects.mutates_inputs')
            if not (native or sem.get('solve_effects') or sem.get('string_unit')):
                continue
            if sem.get('solve_effects'):
                report.expect(sem['solve_effects'] == {'inputMutation': 'forbidden', 'outputAliasing': 'forbidden'},
                              where, 'solve_effects forbids input mutation and output aliasing')
            rows = cases.build_cases(pid, include_maximum=True)
            path = base / language / f'{pid}.{ext}'
            tree = official['params'] and official['params'][0]['type'] == 'TreeNode'
            if tree:
                if language == 'python':
                    py_tree_checks(report, where, load_module(f'abi_tree_{pid}', path), official['name'], rows)
                else:
                    got = node(JS_TREE, {'path': str(path), 'official': official['name'], 'cases': rows})
                    for i, (row, g) in enumerate(zip(rows, got['res'])):
                        report.expect(g['intact'], f'{where}:case{i}', 'solve leaves native TreeNode input intact')
                        report.expect(g['aliased'] == 0, f'{where}:case{i}', f"solve output shares no input node; shared={g['aliased']}")
                        report.expect(g['solve'] == row['expected'], f'{where}:case{i}', 'solve result on native input')
                        report.expect(g['native'] == row['expected'], f'{where}:case{i}', 'native entry result')
                    report.expect(got['cycle'] == 'rejected', f'{where}:cycle', 'solve rejects a cyclic node graph')
                continue
            if language == 'python':
                m = load_module(f'abi_calls_{base.name}_{pid}'.replace('-', '_'), path)
                got = []
                for row in rows:
                    a = copy.deepcopy(row['args'])
                    value = m.solve(*a)
                    b = copy.deepcopy(row['args'])
                    nret = getattr(m.Solution(), official['name'])(*b)
                    got.append({'value': value, 'after': a, 'nativeAfter': b, 'nativeReturn': nret})
            else:
                got = node(JS_CALLS, {'path': str(path), 'official': official['name'], 'cases': [r['args'] for r in rows]})
            for i, (row, g) in enumerate(zip(rows, got)):
                w = f'{where}:case{i}'
                report.expect(g['after'] == row['args'], w, 'solve leaves arguments unchanged')
                report.expect(g['value'] == row['expected'], w, 'solve returns the expected value')
                if in_place is not None:
                    others = [j for j in range(len(row['args'])) if j != in_place]
                    report.expect(g['nativeAfter'][in_place] == row['expected'], w,
                                  f'native entry leaves args[{in_place}] equal to the expected value')
                    report.expect(all(g['nativeAfter'][j] == row['args'][j] for j in others), w,
                                  'native entry leaves every other argument unchanged')
                    report.expect(g['nativeReturn'] is None, w, 'void native entry returns nothing')
                else:
                    report.expect(g['nativeAfter'] == row['args'], w, 'native entry leaves arguments unchanged')
                    report.expect(g['nativeReturn'] == row['expected'], w, 'native entry returns the expected value')
            if sem.get('string_unit') == 'unicode_codepoint':
                canaries = [i for i, row in enumerate(rows)
                            if any(isinstance(a, str) and any(ord(ch) > 0xFFFF for ch in a) for a in row['args'])]
                report.expect(bool(canaries), where, 'string_unit unicode_codepoint has non-BMP canary cases')
                for i in canaries:
                    report.expect(got[i]['value'] == rows[i]['expected'], f'{where}:case{i}',
                                  'non-BMP canary returns the code-point oracle value')
            elif any(isinstance(a, str) and any(ord(ch) > 0xFFFF for ch in a) for row in rows for a in row['args']):
                report.expect(False, where, 'non-BMP case without a declared string_unit')


def historical_bytes(base, relative, digest):
    """Bytes with this hash from disk, a history blob or Git history of the path; None if unrecoverable."""
    current = base / relative
    if current.exists() and sha(current.read_bytes()) == digest:
        return current.read_bytes()
    blob = base / 'study-history/blobs' / f'{digest}.bin'
    if blob.exists():
        data = blob.read_bytes()
        return data if sha(data) == digest else None
    rel = str((base / relative).relative_to(ROOT))
    revisions = subprocess.run(['git', 'log', '--format=%H', '--', rel], cwd=ROOT, capture_output=True,
                               text=True).stdout.split()
    for revision in revisions:
        shown = subprocess.run(['git', 'show', f'{revision}:{rel}'], cwd=ROOT, capture_output=True)
        if shown.returncode == 0 and sha(shown.stdout) == digest:
            return shown.stdout
    return None


def retrievable(base, relative, digest):
    return historical_bytes(base, relative, digest) is not None


def check_lineage(report, base):
    where = f'{base.name}:lineage'
    manifest_raw = (base / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    files = {f['path']: f['sha256'] for f in manifest['files']}
    for path, digest in files.items():
        report.expect(sha((base / path).read_bytes()) == digest, where, f'manifest files hash for {path}')
    for line in (base / 'SHA256SUMS').read_text().splitlines():
        digest, path = line.split('  ', 1)
        report.expect(sha((base / path).read_bytes()) == digest, where, f'SHA256SUMS hash for {path}')
    for row in manifest['source_inventory']:
        tag = f"{row['id']}-{row['language']}"
        source = sha((base / row['path']).read_bytes())
        semantics_raw = (base / row['semantics_path']).read_bytes()
        report.expect(row['sha256'] == source == files.get(row['path']), where, f'source_inventory source hash {tag}')
        report.expect(row['semantics_sha256'] == sha(semantics_raw) == files.get(row['semantics_path']), where,
                      f'source_inventory semantics hash {tag}')
        report.expect(json.loads(semantics_raw)['source_sha256'] == source, where, f'semantics source_sha256 {tag}')
        for old in row.get('supersedes', []):
            report.expect(old['sha256'] != source or old['semantics_sha256'] != row['semantics_sha256'], where,
                          f'supersedes {tag} names different bytes')
            if old['sha256'] != source:
                report.expect(retrievable(base, row['path'], old['sha256']), where,
                              f"superseded source {tag} {old['sha256'][:12]} retrievable")
            if old['semantics_sha256'] != row['semantics_sha256']:
                report.expect(retrievable(base, row['semantics_path'], old['semantics_sha256']), where,
                              f"superseded semantics {tag} {old['semantics_sha256'][:12]} retrievable")
    catalog = json.loads((base / 'authoring-catalog.json').read_text())
    contracts = contract_rows(base)
    rows = {(r['id'], r['language']): r for r in manifest['source_inventory']}
    report.expect(len(catalog['variants']) == len(rows) == catalog['variant_count'], where, 'one catalog variant per inventory row')
    for variant in catalog['variants']:
        tag = f"{variant['problem_id']}-{variant['language']}"
        row = rows[(variant['problem_id'], variant['language'])]
        report.expect(variant['source_sha256'] == row['sha256'] and variant['semantics_sha256'] == row['semantics_sha256'],
                      where, f'catalog variant hashes equal source_inventory {tag}')
        report.expect(variant['problem_contract_sha256'] == sha(compact(contracts[variant['problem_id']])), where,
                      f'catalog problem_contract_sha256 equals the current contracts row {tag}')
        report.expect(variant['variant_id'] in catalog['index'][str(variant['problem_id'])][variant['language']], where,
                      f'catalog index lists the current variant {tag}')
        prior = variant.get('supersedes', [])
        report.expect(len(prior) == len(row.get('supersedes', [])), where, f'catalog and inventory supersedes lengths {tag}')
        for old_variant, old_row in zip(prior, row.get('supersedes', [])):
            report.expect(old_variant['variant_id'] == old_row['catalog_variant_id'] and
                          old_variant['source_sha256'] == old_row['sha256'] and
                          old_variant['semantics_sha256'] == old_row['semantics_sha256'], where,
                          f'catalog supersedes matches inventory supersedes {tag}')
        if prior:
            record = {k: v for k, v in variant.items() if k not in ('variant_id', 'supersedes')}
            report.expect(variant['variant_id'] == sha(compact(record)), where, f'revised variant id rule {tag}')
            # A later revision rewrites manifest.json; the pinned manifest must still be recoverable
            # and must list this variant's current hashes (refreshing provenance would change the ID).
            bound = False
            for p in variant['provenance']:
                pinned = historical_bytes(base, 'manifest.json', p['manifest_sha256'])
                if pinned is not None:
                    bound = bound or any(r['id'] == variant['problem_id'] and r['language'] == variant['language'] and
                                         r['sha256'] == variant['source_sha256'] and
                                         r['semantics_sha256'] == variant['semantics_sha256']
                                         for r in json.loads(pinned)['source_inventory'])
            report.expect(bound, where, f'revised variant provenance pins a recoverable manifest listing its hashes {tag}')
    freeze = json.loads((base / 'pre-source-reference-freeze.json').read_text())
    chains = {}
    for amendment in freeze.get('amendments', []):
        path = amendment['file']
        start = chains.get(path, freeze['files'].get(path))
        if start is not None:
            report.expect(amendment['old_sha256'] == start, where, f'freeze amendment chain continuous for {path}')
        chains[path] = amendment['new_sha256']
    for path, digest in chains.items():
        report.expect(sha((base / path).read_bytes()) == digest, where, f'freeze amendment chain ends at current {path}')
    for path, digest in freeze.get('current_sha256', {}).items():
        report.expect(sha((base / path).read_bytes()) == digest, where, f'freeze current_sha256 for {path}')
    for path, digest in freeze['files'].items():
        if path not in chains:
            report.expect(sha((base / path).read_bytes()) == digest, where, f'frozen file unchanged or amended: {path}')


def main():
    report = Report()
    check_875(report)
    for cohort in COHORTS:
        base = AUTHORED / cohort
        contracts = contract_rows(base)
        cases = load_module('abi_cases_' + cohort.replace('-', '_'), base / 'cases.py')
        check_shape(report, base, contracts)
        check_effects(report, base, contracts, cases)
        check_lineage(report, base)
    result = {'schema': 'gamma.native-abi-regression-check.v1', 'qualification': 'unknown',
              'scope': 'regression gate over declared contracts; not a purity proof or catalogue qualification',
              'checks': report.checks, 'failures': report.failures, 'passed': not report.failures}
    json.dump(result, sys.stdout, indent=1)
    print()
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
