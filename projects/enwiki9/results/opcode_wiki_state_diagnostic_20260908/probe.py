#!/usr/bin/env python3
"""Synthetic inspection of unchanged decoder-visible wiki coordinates."""
import hashlib
import json
import lzma
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = {
    'programs/opcode_typed_anchor_bitmix_v1/p': '3e9c9ed25997ad10bac94575fb3da5009530ba04fa961da14a016fe89eec9a15',
    'programs/opcode_field_compact_v1/p': '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8',
}
CASES = (
    ('link', b'[[Oakford', {'w': 1}),
    ('category', b'[[Category:Trees', {'w': 1, 'slot': 1}),
    ('image', b'[[Image:Oak.jpg', {'w': 1, 'slot': 2}),
    ('cite', b'{{cite', {'w': 2, 'slot': 3}),
    ('infobox', b'{{infobox', {'w': 2, 'slot': 4}),
    ('template-url', b'{{cite|url=', {'w': 2, 'slot': 7}),
    ('template-title', b'{{cite|title=', {'w': 2, 'slot': 8}),
    ('reference-name', b'<ref name="', {'w': 3, 'slot': 6}),
    ('closed-link', b'[[Oakford]]', {'w': 0, 'slot': 0}),
    ('literal-zero', b'\0ordinary', {'w': 0, 'slot': 0}),
    ('xml-field-control', b'<title>Oakford', {'f': 1}),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: probe.py NEW_OUTPUT_DIRECTORY')
    os.sched_setaffinity(0, {3})
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (30,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2,) * 2)
    started = time.monotonic()
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=False)
    sources = {}
    for path, expected in BINDINGS.items():
        data = (ROOT / path).read_bytes()
        if digest(data) != expected:
            raise ValueError('source changed: ' + path)
        sources[path] = data
    rows = []
    for name, raw, expected in CASES:
        parent = {'__name__': 'unchanged_raw_state'}
        compact = {'__name__': 'unchanged_compact_state'}
        exec(compile(lzma.decompress(sources[next(iter(BINDINGS))]), '<parent>', 'exec'), parent)
        exec(compile(lzma.decompress(sources['programs/opcode_field_compact_v1/p']), '<compact>', 'exec'), compact)
        modeled = compact['oe'](raw)
        if compact['od'](modeled) != raw:
            raise ValueError('frontend inverse differs')
        compact['_limit'] = len(modeled)
        before, after = parent['GST'](), compact['GST']()
        for byte in raw:
            before.up(byte)
        for byte in modeled:
            after.up(byte)
        baseline = {key: getattr(before, key) for key in ('f', 'w', 'slot', 'pg')}
        actual = {key: getattr(after, key) for key in baseline}
        if any(baseline[key] != value for key, value in expected.items()):
            raise ValueError('predefined raw-state expectation differs: ' + name)
        rows.append(dict(name=name, raw_hex=raw.hex(), modeled_hex=modeled.hex(),
                         raw_state=baseline, opcode_state=actual, expected=expected,
                         expected_coordinates_match=all(actual[k] == v for k, v in expected.items()),
                         exact_frontend_inverse=True))
    receipt = dict(schema='gamma.enwiki9.opcode-wiki-state-synthetic.v1',
        source_bindings=BINDINGS, probe_sha256=digest(Path(__file__).read_bytes()),
        populations='eleven predefined synthetic strings; no corpus read',
        cases=rows, changed_codec_source=False, compression_executed=False,
        elapsed_seconds=time.monotonic()-started,
        peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        bounds=dict(cpu=3, threads=1, cpu_seconds=30, address_space_bytes=512*1024**2,
                    file_bytes=1024**2, outer_wall_seconds=40),
        conclusion='These synthetic coordinates diagnose an existing representation/state mismatch. Raw-state behavior is the historical detector, not a general XML/wiki parser specification. No archive saving or corpus opportunity frequency was measured.',
        next_test='After current compact parity closure and valid reflection, freeze one wiki-coordinate repair with P/K/D controls. Preserve literal histories, coder, model laws and copy search; all copied and literal bytes update the same state. Separate package costs and select only on development evidence.')
    with (out / 'receipt.json').open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2); stream.write('\n')
    print(json.dumps({'cases': len(rows), 'mismatches': sum(not r['expected_coordinates_match'] for r in rows),
                      'receipt': str(out/'receipt.json')}))


if __name__ == '__main__':
    main()
