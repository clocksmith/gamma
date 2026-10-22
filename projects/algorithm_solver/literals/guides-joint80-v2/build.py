"""Build the joint80 7-bit v2 guide package from the matched80-v2 polish-128 result.

Usage: python3 build.py <published-v1-guides.json>
The argument lists the 80 (problem_id, source_sha256) pairs of the live
bits-literal-joint80-7-v1 guides, exported from BITS, so the package can prove every
source is one already published. Refuses to overwrite an existing package.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIT = ROOT.parent
RUN = LIT / 'matched80-v2/run-v1/polish-128'
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
    package = {
        'schema': 'gamma.literal-guide-package.v1',
        'version': 'bits-literal-joint80-7-v2',
        'supersedes': 'bits-literal-joint80-7-v1',
        'width': 7, 'entries': len(vocab),
        'experiment': {'path': 'projects/algorithm_solver/literals/matched80-v2', 'frozen_commit': 'e1152485e', 'results_commit': '4d29bfb4a',
                       'arm': 'polish-128', 'promotion_rule': 'projects/algorithm_solver/literals/BITS_PROMOTION.md'},
        'dictionary': vocab, 'dictionary_ltd_sha256': sha(raw),
        'published_v1_sources': published,
        'programs': programs,
        'metrics': {k: manifest['metrics'][k] for k in ('selections', 'median_selections', 'p95_selections', 'worst_selections',
                                                        'dictionary_bytes', 'packet_bytes', 'package_bytes', 'single_character_selection_fraction')},
        'promotion': {'live': {'version': 'bits-literal-joint80-7-v1', 'selections': 10155, 'package_bytes': 13002},
                      'selection_change': (manifest['metrics']['selections'] - 10155) / 10155,
                      'package_change': (manifest['metrics']['package_bytes'] - 13002) / 13002},
        'scope': 'Offline encodings of 80 already-published, qualified compact development sources. Not autonomous synthesis, human fluency or M1 qualification.',
    }
    out.write_text(json.dumps(package, indent=1) + '\n')
    (ROOT / 'dictionary.ltd').write_bytes(raw)
    print(json.dumps({'programs': len(programs), 'selections': package['metrics']['selections'], 'package_bytes': package['metrics']['package_bytes']}))


if __name__ == '__main__':
    main()
