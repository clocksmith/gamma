"""Build the joint80 8-bit v2 guide package from the matched80-v3 promotion candidate.

Usage: python3 build.py <published-v1-guides.json>
The argument lists the 80 (problem_id, source_sha256) pairs of the live
bits-literal-joint80-8-v1 guides, exported from BITS, so the package can prove every
source is one already published. Refuses to overwrite an existing package.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIT = ROOT.parent
ARM = 'ils-256-s2'
RUN = LIT / 'matched80-v3/run-v1' / ARM
LIVE = {'version': 'bits-literal-joint80-8-v1', 'selections': 6413, 'package_bytes': 11781}
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    out = ROOT / 'package.json'
    if out.exists():
        raise SystemExit('refusing to overwrite package.json')
    published = {str(pid): digest for pid, digest in json.loads(Path(sys.argv[1]).read_text())}
    manifest = json.loads((RUN / 'manifest.json').read_text())
    vocab = json.loads((RUN / 'dictionary.json').read_text())
    raw = (RUN / 'dictionary.ltd').read_bytes()
    programs = [{'problem_id': row['id'], 'variant': row['variant'], 'source_sha256': row['source_sha256'], 'ids': row['sequence'],
                 'selections': row['selections'], 'packet_sha256': row['packet_sha256']} for row in sorted(manifest['programs'], key=lambda r: r['id'])]
    m = manifest['metrics']
    package = {
        'schema': 'gamma.literal-guide-package.v1',
        'version': 'bits-literal-joint80-8-v2',
        'supersedes': LIVE['version'],
        'width': 8, 'entries': len(vocab),
        'experiment': {'path': 'projects/algorithm_solver/literals/matched80-v3', 'frozen_commit': 'a24b8c0f3', 'results_commit': '4773b2d0b',
                       'arm': ARM, 'promotion_rule': 'projects/algorithm_solver/literals/BITS_PROMOTION.md'},
        'dictionary': vocab, 'dictionary_ltd_sha256': sha(raw),
        'published_v1_sources': published,
        'programs': programs,
        'metrics': {k: m[k] for k in ('selections', 'median_selections', 'p95_selections', 'worst_selections',
                                      'dictionary_bytes', 'packet_bytes', 'package_bytes', 'single_character_selection_fraction')},
        'promotion': {'live': LIVE, 'selection_change': (m['selections'] - LIVE['selections']) / LIVE['selections'],
                      'package_change': (m['package_bytes'] - LIVE['package_bytes']) / LIVE['package_bytes']},
        'scope': 'Offline encodings of 80 already-published, qualified compact development sources: an improved representation of the same programs, not broader problem coverage, autonomous synthesis, human fluency or M1 qualification.',
    }
    out.write_text(json.dumps(package, indent=1) + '\n')
    (ROOT / 'dictionary.ltd').write_bytes(raw)
    print(json.dumps({'programs': len(programs), 'selections': m['selections'], 'package_bytes': m['package_bytes']}))


if __name__ == '__main__':
    main()
