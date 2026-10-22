"""Independently verify package.json; writes verification.json. Executes no candidate source.

Checks: dictionary bytes decode to the listed entries; every packet rebuilt from its IDs
decodes, through the canonical codec, to the exact source; every sequence is a minimum
parse (forward shortest-path oracle written here, independent of the search parser);
every source has passing verdicts in both qualification receipts and equals the
published v1 guide source; selection and byte totals reconcile.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIT = ROOT.parent
SCALE = LIT / 'scale-v2'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
spec = importlib.util.spec_from_file_location('canonical_codec', LIT / 'readable-v1/literal_codec.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)


def minimum_parse(source, entries):
    """Forward DP over byte positions: fewest entries whose concatenation is exactly source."""
    best = [math.inf] * (len(source) + 1)
    best[0] = 0
    for pos in range(len(source)):
        if best[pos] == math.inf:
            continue
        for entry in entries:
            if source.startswith(entry, pos) and best[pos] + 1 < best[pos + len(entry)]:
                best[pos + len(entry)] = best[pos] + 1
    return best[-1]


def main():
    package = json.loads((ROOT / 'package.json').read_text())
    raw = (ROOT / 'dictionary.ltd').read_bytes()
    entries = [s.encode() for s in package['dictionary']]
    assert codec.decode_dictionary(raw) == entries, 'dictionary bytes do not match entries'
    assert sha(raw) == package['dictionary_ltd_sha256'] and len(entries) == package['entries'] <= 2 ** package['width']
    manifest = {(r['id'], r['variant']): r for r in json.loads((SCALE / 'generated/manifest.json').read_text())['rows']}
    receipts = {name: {(r['id'], r['variant']): r for r in json.loads((SCALE / rel).read_text())['rows']}
                for name, rel in (('stored', 'qualification/report.json'), ('rerun', 'qualification-rerun-v1/report.json'))}
    width, packets, selections, checks = package['width'], 0, 0, 0
    for program in package['programs']:
        key = (program['problem_id'], program['variant'])
        source = (SCALE / 'generated' / manifest[key]['file']).read_bytes()
        assert sha(source) == program['source_sha256'] == manifest[key]['sha256'], f'source hash {key}'
        for name, rows in receipts.items():
            verdict = rows[key]
            assert verdict['sha256'] == program['source_sha256'] and verdict['passed'] and not verdict['failures'], f'{name} receipt {key}'
        assert package['published_v1_sources'][str(program['problem_id'])] == program['source_sha256'], f'not the published source {key}'
        packet = codec.packet(program['ids'], width, raw)
        assert sha(packet) == program['packet_sha256'], f'packet hash {key}'
        codec.verify_packet(packet, raw, entries, source)
        assert len(program['ids']) == program['selections'] == minimum_parse(source.decode(), package['dictionary']), f'not a minimum parse {key}'
        packets += len(packet)
        selections += program['selections']
        checks += 1
    m = package['metrics']
    assert len(package['programs']) == 80 == len(package['published_v1_sources']) and checks == 80
    assert selections == m['selections'] and packets == m['packet_bytes'] and len(raw) == m['dictionary_bytes'] and len(raw) + packets == m['package_bytes']
    result = {'schema': 'gamma.literal-guide-verification.v1', 'package_sha256': sha((ROOT / 'package.json').read_bytes()),
              'verifier_sha256': sha(Path(__file__).read_bytes()), 'programs_verified': checks, 'selections': selections,
              'package_bytes': len(raw) + packets, 'all_sources_published_in_v1': True, 'minimum_parse_checked': True,
              'receipts_checked': ['stored', 'rerun']}
    (ROOT / 'verification.json').write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
