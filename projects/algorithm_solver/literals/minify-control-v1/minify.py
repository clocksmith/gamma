"""Om: compaction-only versions of the frozen 500's admitted originals (FREEZE.md).

  minify.py generate --work DIR     terser 5.46.1, no compress, no mangle, comments dropped; writes DIR/minify/om/<id>.js
  minify.py qualify  --work DIR     strict parity with the original on every frozen case; writes DIR/minify/receipt.json
  minify.py pin                     print the terser package hash (pinned in contract.json)

Generation runs once and nobody edits its output. A failing Om falls back to O for that problem in
control.py; the failure stays in the receipt and in every denominator.
"""
import argparse, concurrent.futures, hashlib, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path.insert(0, str(LIT / 'admission500-v1')); sys.path.insert(0, str(LIT / 'style150-v1'))
from stage import sha, write, LIMITS
import style

FROZEN_SHA = '0d6cb3ff8c7bbe86909cf2d240c1bbac93d22652bedb076c45e1b142b27f4110'
TERSER = Path('/usr/share/nodejs/terser')
COMMAND = ['/usr/bin/node', str(TERSER / 'bin/terser'), '--comments', 'false']


def terser_sha():
    h = hashlib.sha256()
    for f in sorted(p for p in TERSER.rglob('*') if p.is_file()):
        h.update(str(f.relative_to(TERSER)).encode() + b'\0' + hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def population(work):
    """All 500 manifest rows, bound to the frozen population hash."""
    frozen = json.loads((LIT / 'admission500-v1/evidence/population-500.json').read_text())
    assert sha((LIT / 'admission500-v1/evidence/population-500.json').read_bytes()) == FROZEN_SHA
    raw = (work / 'population500/manifest.json').read_bytes(); assert sha(raw) == frozen['manifest_sha256']
    rows = {r['id']: r for r in json.loads(raw)['rows']}
    assert len(rows) == 500
    return rows


def shim(work):
    """style.parity reads DIR/population and DIR/population-baseline; point it at the 500 copies."""
    d = work / 'minify' / 'shim'
    if not d.exists():
        d.mkdir(parents=True)
        (d / 'population').symlink_to(work / 'population500'); (d / 'population-baseline').symlink_to(work / 'population500-baseline')
    return d


def generate(work):
    rows = population(work); out = work / 'minify' / 'om'; out.mkdir(parents=True, exist_ok=False)
    for pid in sorted(rows):
        src = work / 'population500' / f'{pid}.js'
        res = subprocess.run(COMMAND + [str(src)], capture_output=True, check=True)
        (out / f'{pid}.js').write_bytes(res.stdout)
    write(work / 'minify' / 'generation.json', {'terser_version': '5.46.1', 'terser_sha256': terser_sha(), 'command': COMMAND[1:],
                                               'node': subprocess.run(['/usr/bin/node', '--version'], capture_output=True, text=True).stdout.strip(),
                                               'files': {str(pid): sha((out / f'{pid}.js').read_bytes()) for pid in sorted(rows)}})
    print(len(rows), 'generated')


def check(work, pid, text, row):
    return style.parity(shim(work), pid, text, row['entry'], row, None)


def qualify(work):
    rows = population(work); om = work / 'minify' / 'om'
    gen = json.loads((work / 'minify' / 'generation.json').read_text())
    assert gen['terser_sha256'] == terser_sha()
    shim(work); results = {}
    with concurrent.futures.ProcessPoolExecutor(LIMITS['workers']) as pool:
        futs = {}
        for pid in sorted(rows):
            text = (om / f'{pid}.js').read_text(); assert sha(text.encode()) == gen['files'][str(pid)]
            futs[pool.submit(check, work, pid, text, rows[pid])] = (pid, text)
        for f in concurrent.futures.as_completed(futs):
            pid, text = futs[f]; passed, ok, n, bad = f.result()
            original = (work / 'population500' / f'{pid}.js').read_bytes()
            results[pid] = {'id': pid, 'passed': passed, 'sha256': sha(text.encode()), 'bytes': len(text.encode()),
                            'original_sha256': sha(original), 'original_bytes': len(original), 'checks': f'{ok}/{n}',
                            'failure': None if passed else (bad[0] if bad else 'unknown')}
    rows_out = [results[p] for p in sorted(results)]
    write(work / 'minify' / 'receipt.json', {'generation_sha256': sha((work / 'minify' / 'generation.json').read_bytes()),
                                            'passed': sum(r['passed'] for r in rows_out), 'rows': rows_out})
    print(sum(r['passed'] for r in rows_out), 'of', len(rows_out), 'qualify;',
          sum(r['bytes'] for r in rows_out), 'bytes vs', sum(r['original_bytes'] for r in rows_out), 'original')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('step', choices=['generate', 'qualify', 'pin']); ap.add_argument('--work', type=Path)
    a = ap.parse_args()
    if a.step == 'pin': print(terser_sha())
    else: {'generate': generate, 'qualify': qualify}[a.step](a.work.resolve())
