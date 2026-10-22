"""Independent checks of every sixbit-v1 output; shares no code with model.py or run.py.

- Sources: rebuilt from the scale-v2 manifest and both qualification receipts.
- Vocabularies: rule W or U checked directly against the 80 texts; budgets checked.
- Packets: canonical LTV1 (bitpack.decode and literal_codec.verify_packet) for A and B;
  the charged reference decoder for C. Selections, escapes and presses are recounted
  from the packet bits.
- Bounds: a Lagrangian bound recomputed from the stored node potentials over every
  eligible substring of every program (not over the solver's model). Any potentials
  give a valid bound, so this check does not trust the LP solver.
"""
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LITERALS = ROOT.parent
sys.path[:0] = [str(LITERALS), str(LITERALS / 'pass2/working')]
from bitpack import decode as ltv_decode

spec = importlib.util.spec_from_file_location('literal_codec', LITERALS / 'readable-v1/literal_codec.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
spec = importlib.util.spec_from_file_location('escape6_decoder', ROOT / 'escape6_decoder.py')
escape_decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(escape_decoder)
sha = lambda b: hashlib.sha256(b).hexdigest()
ESCAPABLE = {10} | set(range(32, 127))
BUDGET = {'A': None, 'B': 64, 'C': 63}


def sources(style):
    scale = LITERALS / 'scale-v2'
    manifest = (scale / 'generated/manifest.json').read_bytes()
    ids = set(json.loads((LITERALS / 'matched80-v1/labels/ids.json').read_text()))
    receipts = [json.loads((scale / r).read_text()) for r in ('qualification/report.json', 'qualification-rerun-v1/report.json')]
    texts, hashes = {}, {}
    for row in json.loads(manifest)['rows']:
        if row['variant'] != style or row['id'] not in ids:
            continue
        raw = (scale / 'generated' / row['file']).read_bytes()
        assert sha(raw) == row['sha256']
        for receipt in receipts:
            assert receipt['generated_manifest_sha256'] == sha(manifest)
            verdict = [r for r in receipt['rows'] if r['id'] == row['id'] and r['variant'] == style]
            assert len(verdict) == 1 and verdict[0]['passed'] and not verdict[0]['failures'] and verdict[0]['sha256'] == row['sha256']
        texts[str(row['id'])], hashes[str(row['id'])] = raw.decode('utf-8'), row['sha256']
    assert len(texts) == 80
    return texts, hashes


def eligible(rule, texts):
    whole = set(texts.values())
    def check(s):
        if not s or s in whole or not any(s in t for t in texts.values()):
            return False
        if rule == 'U' or len(s) == 1:
            return True
        return len(s.encode('utf-8')) <= 160 and sum(s in t for t in texts.values()) >= 2
    return check


def lagrangian(texts, rule, kind, certificate, budget=None):
    """Exact bound (as integer numerator over `scale`) for the stated kind.

    A: entries >= bound. B1: uncovered programs >= bound. C: presses >= bound.
    For every eligible string s the term is min(0, kappa - sum over occurrences (i, j)
    of max(0, pi_i - pi_j - sigma)); kappa is the entry cost (1 for A, the budget
    multiplier mu for B1 and C) and sigma the per-selection cost (7 presses for C)."""
    scale, mu, pot = certificate['scale'], certificate['mu'], certificate['potentials']
    assert mu >= 0 and set(pot) == set(texts) and all(len(pot[p]) == len(texts[p]) + 1 for p in texts)
    budget = budget if budget is not None else {'B1': 64, 'C': 63}.get(kind)
    kappa = scale if kind == 'A' else mu
    sigma = 7 * scale if kind == 'C' else 0
    if kind == 'A':
        total = sum(pot[p][0] - pot[p][-1] for p in texts)
    elif kind == 'B1':
        total = len(texts) * scale - budget * mu + sum(min(0, pot[p][0] - pot[p][-1] - scale) for p in texts)
    else:
        total = sum(pot[p][0] - pot[p][-1] for p in texts) - budget * mu
        for p, t in texts.items():
            total += sum(min(0, 15 * scale - pot[p][i] + pot[p][i + 1]) for i in range(len(t)) if ord(t[i]) in ESCAPABLE)
    whole = set(texts.values())
    longest = max(map(len, texts.values())) if rule == 'U' else 160
    for length in range(1, longest + 1):
        drops, owners = defaultdict(int), defaultdict(set)
        for p, t in texts.items():
            pi = pot[p]
            for i in range(len(t) - length + 1):
                s = t[i:i + length]
                drops[s] += max(0, pi[i] - pi[i + length] - sigma)
                owners[s].add(p)
        for s, drop in drops.items():
            if s in whole or (rule == 'W' and length > 1 and len(owners[s]) < 2):
                continue
            total += min(0, kappa - drop)
    return total, scale


def ceil_div(a, b):
    return -((-a) // b)


def check_job(folder, texts, hashes):
    m = json.loads((folder / 'manifest.json').read_text())
    rule, kind = m['rule'], m['experiment']
    report = {'job': m['job'], 'rule': rule, 'experiment': kind}
    ok = eligible(rule, texts)
    vocabulary = m.get('vocabulary')
    if vocabulary is not None:
        assert all(ok(s) for s in vocabulary), 'vocabulary violates its rule'
        assert len(set(vocabulary)) == len(vocabulary)
        if BUDGET[kind] is not None:
            assert len(vocabulary) <= BUDGET[kind], 'budget exceeded'
        report['entries'] = len(vocabulary)
    cert = folder / 'certificate.json'
    if cert.exists():
        certificate = json.loads(cert.read_text())
        bound, scale = lagrangian(texts, rule, {'A': 'A', 'B': 'B1', 'C': 'C'}[kind], certificate)
        report['bound'] = bound / scale
        if kind == 'A':
            report['min_entries_at_least'] = ceil_div(bound, scale)
            report['six_bit_exact_coverage_impossible'] = ceil_div(bound, scale) > 64
            if vocabulary is not None:
                report['optimum_proven'] = ceil_div(bound, scale) == len(vocabulary)
        elif kind == 'B':
            report['coverage_at_most'] = len(texts) - ceil_div(bound, scale)
        else:
            report['presses_at_least'] = ceil_div(bound, scale)
    if kind in ('A', 'B') and (folder / 'dictionary.ltd').exists():
        dictionary = (folder / 'dictionary.ltd').read_bytes()
        literals = [s.encode() for s in m['package']['entries']]
        covered, selections = [], {}
        for packet in sorted((folder / 'packets').glob('*.ltv')):
            p, raw = packet.stem, packet.read_bytes()
            source = texts[p].encode()
            codec.verify_packet(raw, dictionary, literals, source)
            assert ltv_decode(dictionary, raw) == source
            assert raw[4] == 6 and sha(source) == hashes[p]
            selections[p] = int.from_bytes(raw[37:41], 'big')
            covered.append(p)
        report.update(covered=len(covered), selections=sum(selections.values()), presses=7 * sum(selections.values()),
                      package_bytes=len(dictionary) + sum((folder / 'packets' / f'{p}.ltv').stat().st_size for p in covered))
        assert selections == {p: v for p, v in m['selections'].items() if p in selections}
        if kind == 'A' and len(vocabulary) <= 64:
            assert len(covered) == 80
    if kind == 'A' and vocabulary is not None:
        # Exact cover check that does not need packets (also for vocabularies over 64).
        def covers(t):
            reach = [True] + [False] * len(t)
            for i in range(len(t)):
                if reach[i]:
                    for s in vocabulary:
                        if t.startswith(s, i):
                            reach[i + len(s)] = True
            return reach[-1]
        report['vocabulary_covers_all'] = all(covers(t) for t in texts.values())
    if kind == 'C':
        dictionary = (folder / 'dictionary.ltd').read_bytes()
        presses = escapes = tokens = 0
        for p in texts:
            raw = (folder / 'packets' / f'{p}.lte').read_bytes()
            assert escape_decoder.decode(dictionary, raw) == texts[p] and sha(texts[p].encode()) == hashes[p]
            bits, pos = ''.join(format(b, '08b') for b in raw[40:]), 0
            for _ in range(int.from_bytes(raw[36:40], 'big')):
                if int(bits[pos:pos + 6], 2) == 63:
                    escapes += 1
                    presses += 15
                    pos += 13
                else:
                    presses += 7
                    pos += 6
                tokens += 1
        decoder = (ROOT / 'escape6_decoder.py').stat().st_size
        packets = sum((folder / 'packets' / f'{p}.lte').stat().st_size for p in texts)
        report.update(covered=80, presses=presses, escapes=escapes, selections=tokens - escapes,
                      package_bytes=decoder + len(dictionary) + packets, package_bytes_without_decoder=len(dictionary) + packets)
        assert presses == m['presses'] and escapes == m['escapes']
    return report


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'run-v1'
    results, cache = [], {}
    for job in sorted(p for p in folder.iterdir() if (p / 'manifest.json').exists()):
        style = json.loads((job / 'manifest.json').read_text())['style']
        if style not in cache:
            cache[style] = sources(style)
        results.append(check_job(job, *cache[style]))
        print(json.dumps(results[-1]), flush=True)
    (folder / 'verification.json').write_text(json.dumps(results, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
