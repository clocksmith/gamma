"""Frozen fixed-source attribution and optimistic bounds; private inputs stay local."""
import argparse
import bisect
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path[:0] = [str(LIT), str(LIT / 'pass2/working')]
from literals import shortest_encode, dictionary_bytes
from bitpack import encode, decode


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def distribution(values):
    xs = sorted(values)
    return {'n': len(xs), 'total': sum(xs), 'median': statistics.median(xs),
            'p90': xs[math.ceil(.9 * len(xs)) - 1],
            'p95': xs[math.ceil(.95 * len(xs)) - 1], 'worst': xs[-1],
            'within_32': sum(x <= 32 for x in xs), 'within_96': sum(x <= 96 for x in xs)}


def load_sources(work, contract):
    """Only explicit allowed paths. Never call historical all-500 pool loaders."""
    sources = {}
    for row in contract['sources']:
        raw = (work / row['relative_path']).read_bytes()
        assert sha(raw) == row['sha256'], row['id']
        text = raw.decode('ascii')
        assert len(text) >= 2
        sources[row['id']] = text
    return sources


def attribute(text, vocab, seq, labels):
    frac, exclusive, single, byte_counts = Counter(), Counter(), Counter(), Counter(labels)
    position = 0
    for index in seq:
        piece = vocab[index]
        counts = Counter(labels[position:position + len(piece)])
        assert sum(counts.values()) == len(piece)
        for category, count in counts.items():
            frac[category] += count / len(piece)
        exclusive[next(iter(counts)) if len(counts) == 1 else 'mixed'] += 1
        if len(piece) == 1:
            single[labels[position]] += 1
        position += len(piece)
    assert position == len(text)
    assert math.isclose(sum(frac.values()), len(seq), abs_tol=1e-8)
    return {'fractional_selections': dict(frac), 'exclusive_selections': dict(exclusive),
            'single_character_selections': dict(single), 'source_bytes': dict(byte_counts)}


def lcp(a, b):
    j = 0
    while j < min(len(a), len(b)) and a[j] == b[j]:
        j += 1
    return j


def shared_lengths(sources):
    """Longest cross-program substring at each offset, exact and uncapped.

    In sorted suffix order the nearest suffix with a different owner on each
    side suffices. Repeated suffixes within one owner form contiguous runs.
    """
    suffixes = sorted((text[i:], pid, i) for pid, text in sources.items() for i in range(len(text)))
    result = {pid: [1] * len(text) for pid, text in sources.items()}
    start = 0
    while start < len(suffixes):
        end = start + 1
        while end < len(suffixes) and suffixes[end][1] == suffixes[start][1]:
            end += 1
        neighbors = ([suffixes[start - 1][0]] if start else []) + ([suffixes[end][0]] if end < len(suffixes) else [])
        for suffix, pid, offset in suffixes[start:end]:
            result[pid][offset] = max([1] + [lcp(suffix, other) for other in neighbors])
        start = end
    return result


def relaxed_count(text, lengths):
    """Unlimited matching strings plus free character availability, charged per use.

    Full-source and full-body strings are allowed in the relaxation, then the
    necessary two-selection floor is imposed. This is not a legal dictionary.
    """
    n = len(text)
    dp = [n + 1] * (n + 1)
    dp[n] = 0
    for i in range(n - 1, -1, -1):
        dp[i] = 1 + min(dp[i + 1:i + min(lengths[i], n - i) + 1])
    return max(2, dp[0])


def capacity_bound(base_counts, cap):
    """At most cap programs can use a string unique to that program.

    Relax every shared string and every character as available. A program using
    no private multi-character string costs >= b_p. One private entry belongs
    to only one program, so <= cap programs may beat b_p. Optimistically lower
    the cap largest b_p to 2. Result gives simultaneous sum and quantile lower
    bounds (different optimizers can attain different summaries).
    """
    xs = sorted(base_counts)
    q = min(cap, len(xs))
    return [2] * q + xs[:len(xs) - q]


def fit_oracle(fit, targets):
    suffixes = sorted(text[i:] for text in fit.values() for i in range(len(text)))
    result = {}
    for pid, text in targets.items():
        lengths = []
        for i in range(len(text)):
            suffix = text[i:]
            at = bisect.bisect_left(suffixes, suffix)
            near = suffixes[max(0, at - 1):min(len(suffixes), at + 1)]
            lengths.append(max([1] + [lcp(suffix, other) for other in near]))
        result[pid] = relaxed_count(text, lengths)
    return result


def run(work, output):
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, expected in c['code_hashes'].items():
        assert sha((LIT / rel).read_bytes()) == expected, rel
    assert sha(Path(c['acorn']['file']).read_bytes()) == c['acorn']['sha256']
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    sources = load_sources(work, c)
    labels = json.loads(subprocess.run(['node', str(HERE / 'lexical.cjs')],
                        input=json.dumps(sources), text=True, capture_output=True, check=True).stdout)
    fit_ids, val_ids = c['partition']['dev_fit'], c['partition']['dev_val']
    result = {'schema': 'gamma.cost-decomposition.v1', 'contract_sha256': sha((HERE / 'contract.json').read_bytes()),
              'arms': {}, 'bounds': {}, 'source_files_opened': len(sources), 'heldout_source_files_opened': 0}
    for width in (7, 8):
        pin = c['dictionaries'][str(width)]
        raw = (work / pin['relative_path']).read_bytes()
        assert sha(raw) == pin['sha256']
        vocab = json.loads(raw)
        assert len(vocab) == len(set(vocab)) <= 2 ** width
        assert not set(vocab).intersection(sources.values())
        db = dictionary_bytes(vocab)
        rows = {}
        for pid, text in sources.items():
            seq = shortest_encode(text, vocab)
            packet = encode(vocab, seq, width)
            assert decode(db, packet) == text
            rows[str(pid)] = {'selections': len(seq), 'actions': len(seq) + 1,
                             'packet_bytes': len(packet), 'source_sha256': sha(text.encode()),
                             **attribute(text, vocab, seq, labels[str(pid)])}
        arm = {'dictionary_sha256': sha(raw), 'entries': len(vocab), 'dictionary_bytes': len(db), 'per_problem': rows}
        for name, ids in [('dev_fit', fit_ids), ('dev_val', val_ids)]:
            rr = [rows[str(pid)] for pid in ids]
            cats = {}
            for field in ['fractional_selections','exclusive_selections','single_character_selections','source_bytes']:
                total = Counter()
                for row in rr:
                    total.update(row[field])
                cats[field] = dict(total)
            sel = sum(r['selections'] for r in rr)
            packets = sum(r['packet_bytes'] for r in rr)
            arm[name] = {'selections': distribution([r['selections'] for r in rr]),
                         'actions': distribution([r['actions'] for r in rr]), **cats,
                         'single_character_fraction': sum(cats['single_character_selections'].values()) / sel,
                         'payload_bits': width * sel, 'framing_bytes': 41 * len(ids),
                         'padding_bits': sum((-width * r['selections']) % 8 for r in rr),
                         'packet_bytes': packets, 'package_bytes': len(db) + packets,
                         'submission_actions': len(ids), 'navigation_actions': 0, 'correction_actions': 0}
        assert arm['dev_val']['selections']['total'] == c['expected_dev_val_selections'][str(width)]
        result['arms'][str(width)] = arm
        print(f"width={width} decoded={len(rows)} baseline_reproduced", flush=True)
    lengths = shared_lengths(sources)
    shared = {pid: relaxed_count(text, lengths[pid]) for pid, text in sources.items()}
    oracle = fit_oracle({p: sources[p] for p in fit_ids}, {p: sources[p] for p in val_ids})
    result['bounds']['fit_substring_transfer_oracle'] = {'scope': 'fit-witnessed substrings only; shared cardinality relaxed; not universal M1',
        'dev_val_selections': distribution(list(oracle.values())), 'per_problem': oracle}
    result['bounds']['unlimited_cross_program_shared_oracle'] = {'scope': 'diagnostic using all 400 development sources; not a fitted vocabulary',
        'selections': distribution(list(shared.values())), 'per_problem': shared}
    for cap in (128, 256):
        counts = capacity_bound(list(shared.values()), cap)
        result['bounds'][f'capacity_{cap}'] = {'scope': 'necessary lower bound for arbitrary shared exact-string dictionaries on these fixed 400 sources; not equivalent-source or 500 qualification',
            'selections': distribution(counts), 'actions': distribution([n + 1 for n in counts]),
            'private_program_allowance': cap, 'shared_capacity_relaxed': True,
            'single_character_fraction_lower_bound': 0}
    result['runtime'] = {'python': sys.version, 'seconds': time.monotonic() - started,
                         'decoder_source_bytes': {str(p.relative_to(LIT)): p.stat().st_size for p in [LIT/'literals.py', LIT/'pass2/working/bitpack.py']}}
    write(output / 'results.json', result)
    print(json.dumps({'seconds': result['runtime']['seconds'], 'bounds': {k: {kk: vv for kk, vv in v.items() if kk != 'per_problem'} for k, v in result['bounds'].items()}}), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    run(a.work, a.output)
