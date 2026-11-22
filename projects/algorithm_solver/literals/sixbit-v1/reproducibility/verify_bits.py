"""Extract and solver-free verify the frozen compact BITS proofs (A, B, and C)."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

PIN = '59ff04415ff2afd04ff2ed451340f4f02852bf18'
BASE = 'projects/algorithm_solver/literals/'
SIX = BASE + 'sixbit-v1/'


def unpack_ltd1(raw):
    if raw[:4] != b'LTD1' or len(raw) < 8:
        raise ValueError('LTD1 header')
    count, at, entries = struct.unpack_from('>I', raw, 4)[0], 8, []
    for _ in range(count):
        size = struct.unpack_from('>I', raw, at)[0]
        entries.append(raw[at + 4:at + 4 + size].decode('utf-8'))
        at += 4 + size
    if at != len(raw):
        raise ValueError('LTD1 length')
    return entries


def forced_witness_singletons(texts):
    bigram_docs = defaultdict(set)
    for p, t in texts.items():
        for i in range(len(t) - 1):
            bigram_docs[t[i:i + 2]].add(p)
    forced = set()
    for p, t in texts.items():
        for i, ch in enumerate(t):
            left_shared = i > 0 and len(bigram_docs[t[i - 1:i + 1]]) >= 2
            right_shared = i + 1 < len(t) and len(bigram_docs[t[i:i + 2]]) >= 2
            if not left_shared and not right_shared:
                forced.add(ch)
    return forced


pub = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
if pub is None:
    sys.exit('usage: python3 verify_bits.py PATH_TO_GAMMA_GIT_CHECKOUT')


def git(*args):
    return subprocess.check_output(['git', '-C', str(pub), *args])


assert git('rev-parse', PIN + '^{commit}').decode().strip() == PIN
with tempfile.TemporaryDirectory(prefix='bits-proof-') as d:
    root = Path(d)

    def extract(path):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = git('show', PIN + ':' + path)
        target.write_bytes(raw)
        return raw

    for f in (
        'LICENSE',
        *(SIX + x for x in (
            'README.md', 'FREEZE.md', 'FREEZE-jupiter.md', 'RESULTS.md', 'ESCAPE6.md',
            'contract.json', 'contract-jupiter.json', 'verify.py', 'verify_amended.py',
            'escape6_decoder.py',
        )),
        *(BASE + x for x in (
            'literals.py', 'pass2/working/bitpack.py', 'readable-v1/literal_codec.py',
            'scale-v2/qualification/report.json', 'scale-v2/qualification-rerun-v1/report.json',
        )),
    ):
        extract(f)
    ids = set(json.loads(extract(BASE + 'matched80-v1/labels/ids.json')))
    manifest = json.loads(extract(BASE + 'scale-v2/generated/manifest.json'))
    rows = [r for r in manifest['rows'] if r['variant'] == 'compact' and r['id'] in ids]
    assert len(ids) == len(rows) == 80
    texts = {}
    for r in rows:
        media = extract(BASE + 'scale-v2/generated/' + r['file'])
        assert hashlib.sha256(media).hexdigest() == r['sha256']
        texts[str(r['id'])] = media.decode('utf-8')

    assert len(forced_witness_singletons(texts)) == 74

    arms = {
        'run-v1': ['a-u-compact', 'a-w-compact', 'b-w-compact', 'c-w-compact', 'c-u-compact'],
        'run-jupiter-v1': ['b-u-compact'],
    }
    for run, jobs in arms.items():
        paths = [SIX + run + '/' + j for j in jobs]
        for f in git('ls-tree', '-r', '--name-only', '--full-tree', PIN, '--', *paths).decode().splitlines():
            extract(f)
        subprocess.run([sys.executable, '-B', str(root / SIX / 'verify_amended.py'), str(root / SIX / run)], check=True)
        for j in jobs:
            folder = root / SIX / run / j
            dict_path = folder / 'dictionary.ltd'
            if dict_path.exists():
                jm = json.loads((folder / 'manifest.json').read_text())
                assert unpack_ltd1(dict_path.read_bytes()) == jm['vocabulary']

    rs = {j['job']: j for run in arms for j in json.loads((root / SIX / run / 'verification.json').read_text())}
    assert set(rs) == {j for a in arms.values() for j in a}
    for job, optimum in [('a-u-compact', 79), ('a-w-compact', 92)]:
        j = rs[job]
        assert j['entries'] == j['min_entries_at_least'] == optimum and j['optimum_proven'] and j['vocabulary_covers_all']
    for job in ('b-u-compact', 'b-w-compact'):
        j = rs[job]
        assert j['covered'] == j['coverage_at_most'] == 64 and j['entries'] == 64

    cw = rs['c-w-compact']
    assert cw['entries'] == 63 and cw['presses'] == cw['presses_at_least'] == 75925
    assert 6 * cw['selections'] + 13 * cw['escapes'] == 65236
    assert -((-6 * cw['presses_at_least']) // 7) == 65079

    cu = rs['c-u-compact']
    assert cu['entries'] == 63 and cu['presses'] == 24613 and cu['presses_at_least'] == 24166

    print('PASS: frozen compact U=79, W=92 (74 forced singletons); at 64 entries U=W=64/80; escape W=75925 (raw>=65079, recount 65236), U=24613 (bound 24166).')
