"""Evaluate committed literal dictionaries on the live 80-problem BITS slots (FREEZE.md).

  bridge.py --work DIR --output DIR/bits80-bridge/run-v1

Evaluation only: exact canonical parse of the 80 published compact sources, packets decoded through the
canonical codec, BITS macro rule, whole-program check, per-problem comparison with the live profile."""
import argparse, hashlib, importlib.util, json, statistics, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
BITS = Path('/home/x/deco/256one/public/labs/two-button')
spec = importlib.util.spec_from_file_location('style150_v2_measure', LIT / 'style150-v2/measure.py')
m2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m2)
v3, joint, v1, write = m2.v3, m2.joint, m2.v1, m2.write
LIVE = {7: ('bits-literal-joint80-7-v2', LIT / 'guides-joint80-v2/package.json', 9910, 12798),
        8: ('bits-literal-joint80-8-v2', LIT / 'guides-joint80-8-v2/package.json', 6161, 11750)}
BAR = {7: (9711, 13438), 8: (6037, 12338)}


def sources():
    pub = json.loads((LIT / 'guides-joint80-8-v2/published-8-v1-sources.json').read_text())
    man = json.loads((LIT / 'scale-v2/generated/manifest.json').read_text())
    by_sha = {r['sha256']: r for r in man['rows']}
    out, files = {}, {}
    for pid, h in pub:
        r = by_sha[h]; text = (LIT / 'scale-v2/generated' / r['file']).read_text(); assert sha(text.encode()) == h and r['id'] == pid
        out[pid] = {'compact': text}; files[(pid, 'compact')] = {'file': r['file']}
    assert len(out) == 80
    return out, files


def candidates(work):
    c = []
    for width, size in ((7, 128), (8, 256)):
        for arm in ('A', 'A0', 'B', 'C', 'D', 'E', 'CH', 'DH'):
            c.append(('style150-v1', arm, width, work / f'style150/run-v1/{arm}-{size}/dictionary.json'))
        for arm in ('C', 'D', 'E', 'CH', 'DH'):
            c.append(('style150-v2', arm, width, work / f'style150/run-v2/{arm}-{size}/dictionary.json'))
        for arm in ('W1', 'W2', 'H1', 'H2', *[f'I2-{size}-s{s}' for s in range(1, 6)]):
            name = arm if arm.startswith('I2') else f'{arm}-{size}'
            c.append(('scale500-v1', arm.split('-')[0] + (arm[-3:] if arm.startswith('I2') else ''), width, work / f'scale500/run-v1/{name}/dictionary.json'))
        for pool in ('O', 'Om', 'R'):
            for fit in ('F500', 'Fdev'):
                c.append(('minify-control-v1', f'D_{pool}-{fit}', width, work / f'minify/run-v1/dictionaries/{pool}-{fit}-{size}.json'))
        for pool in ('O', 'Om', 'R'):
            c.append(('structural-v1', f'L-{pool}', width, work / f'structural/run-v1/dictionaries/L-{pool}-{size}.json'))
    return c


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args(); out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    src, files = sources()
    rows, dicts = [], {}
    live = {}
    for width, (name, pkg, sel, size) in LIVE.items():
        p = json.loads(pkg.read_text()); vocab = p['dictionary']
        st = joint.evaluate(src, vocab, width)
        assert (st['selections'], st['package_bytes']) == (sel, size), (name, st['selections'], st['package_bytes'])
        live[width] = {pid: len(st['parsed'][pid, 'compact']) for pid in src}
        rows.append({'experiment': 'live', 'arm': name, 'width': width, 'selections': sel, 'package_bytes': size, 'reproduced': True})
    for exp, arm, width, path in candidates(a.work.resolve()):
        vocab = json.loads(path.read_text()); key = f'{exp}:{arm}:{width}'
        assert len(vocab) <= 2 ** width and set(joint.base.ALPHABET) <= set(vocab), key
        dicts[key] = vocab
        try:
            st = joint.evaluate(src, vocab, width)
        except ValueError as e:
            rows.append({'experiment': exp, 'arm': arm, 'width': width, 'dictionary_sha256': sha(path.read_bytes()), 'error': str(e)}); continue
        met = v3.save(out, key.replace(':', '_'), src, files, st, width, f'bits80-bridge-{key}', v1.provenance_of([]), {'candidate': key})
        per = {pid: len(st['parsed'][pid, 'compact']) for pid in src}
        d = [per[p] - live[width][p] for p in src]
        rows.append({'experiment': exp, 'arm': arm, 'width': width, 'dictionary_sha256': sha(path.read_bytes()),
                     'selections': st['selections'], 'package_bytes': st['package_bytes'], 'packets_verified': met['covered_programs'],
                     'whole_program_literals': met['whole_program_literals'],
                     'vs_live': {'fewer': sum(x < 0 for x in d), 'same': sum(x == 0 for x in d), 'more': sum(x > 0 for x in d),
                                 'median': statistics.median(d), 'min': min(d), 'max': max(d)},
                     'per_problem': {str(p): per[p] for p in sorted(src)}})
    with tempfile.NamedTemporaryFile('w', suffix='.json') as f:
        json.dump(dicts, f); f.flush()
        macros = json.loads(subprocess.run(['/usr/bin/node', str(HERE / 'macros.mjs'), str(BITS), f.name], capture_output=True, check=True).stdout)
    decision = {}
    for r in rows:
        if r['experiment'] == 'live' or 'error' in r: continue
        r['macro_entries'] = macros[f"{r['experiment']}:{r['arm']}:{r['width']}"]
        r['category'] = 'macro' if r['macro_entries'] else 'primitive'
        sb, pb = BAR[r['width']]
        r['passes_gates_1_to_3'] = (r['category'] == 'primitive' and r['packets_verified'] == 80 and r['whole_program_literals'] == 0
                                    and r['selections'] <= sb and r['package_bytes'] <= pb)
    for width in (7, 8):
        ok = sorted((r for r in rows if r.get('passes_gates_1_to_3') and r['width'] == width), key=lambda r: (r['selections'], r['package_bytes']))
        best = min((r for r in rows if r['width'] == width and r['experiment'] != 'live' and 'selections' in r), key=lambda r: (r['selections'], r['package_bytes']))
        decision[width] = {'live': LIVE[width][0], 'bar': BAR[width], 'eligible': f"{ok[0]['experiment']}:{ok[0]['arm']}" if ok else None,
                           'verdict': 'eligible (gates 4-5 and owner go-ahead pending)' if ok else 'not promoted',
                           'best_candidate': {k: best[k] for k in ('experiment', 'arm', 'selections', 'package_bytes', 'category', 'vs_live')}}
    write(out / 'results.json', {'rows': rows, 'decision': decision})
    for r in rows:
        if 'selections' in r:
            print(f"{r['width']} {r['experiment']:18} {r['arm']:14} sel {r['selections']:6} pkg {r['package_bytes']:6} {r.get('category', 'live'):9} "
                  f"{r.get('vs_live', '')}")
        else:
            print(r['width'], r['experiment'], r['arm'], 'ERROR', r['error'])
    print(json.dumps(decision, indent=1))


if __name__ == '__main__':
    main()
