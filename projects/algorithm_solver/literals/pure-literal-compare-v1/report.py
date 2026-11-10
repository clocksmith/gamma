"""Source-free comparisons; never fits a dictionary or opens source payloads."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build():
    first = json.loads((HERE / 'results.json').read_bytes())
    current = json.loads((HERE / 'ascii-results.json').read_bytes())
    macro = json.loads((HERE.parent / 'macro-fragment-compare-v1/results.json').read_bytes())
    comparisons = {}
    for language, data in current['languages'].items():
        comparisons[language] = {}
        for width in ['6', '7', '8']:
            pure = data['validation'][width]
            other = macro['languages'][language]['validation'][width + '-mixed']
            old = {r['id']: r for r in other['rows']}
            covered = [r for r in pure['rows'] if r['status'] == 'represented']
            if any(r['source_sha256'] != old[r['id']]['source_sha256'] for r in covered):
                raise ValueError('Comparison source identities differ')
            payload = sum(r['payload_bits'] for r in covered)
            old_payload = sum(old[r['id']]['payload_bits'] for r in covered)
            packets = sum(r['packet_bytes'] for r in covered)
            old_packets = sum(old[r['id']]['packet_bits'] for r in covered) // 8
            comparisons[language][width] = {'matched_sources': len(covered),
                'pure_payload_bits': payload, 'mixed_payload_bits': old_payload,
                'pure_packet_bytes': packets, 'mixed_packet_bytes': old_packets,
                'payload_change_percent': 100 * (payload / old_payload - 1),
                'packet_change_percent': 100 * (packets / old_packets - 1),
                'pure_dictionary_bytes': pure['summary']['dictionary_bytes'],
                'mixed_dictionary_bytes': other['summary']['dictionary_storage_bytes'],
                'pure_packet_better_equal_worse': [sum((r['packet_bytes'] > old[r['id']]['packet_bits']/8) -
                    (r['packet_bytes'] < old[r['id']]['packet_bits']/8) == sign for r in covered) for sign in [-1, 0, 1]]}
    (HERE / 'comparison.json').write_text(json.dumps(comparisons, sort_keys=True, indent=2) + '\n')
    lines = ['# Pure literal development result', '',
        'Pure 7/8-bit dictionaries reconstruct **all 400 known development programs in each language**,',
        'including all 100 exposed validation programs. This is exact representation of qualified',
        'source, not solving from statements, new native qualification, or 1,000 problems.', '',
        'Each selected code inserts only its stored string. At 7 bits the selected tables contain',
        '98 ordinary ASCII characters and 30 flat merged strings; at 8 bits, 98 characters and',
        '158 merged strings. No spelling mode, macro, free binding or hidden helper exists.',
        'These are compression-first fragments, not a human-tested idiom vocabulary.',
        'Six-bit fitting selects 64 ordinary characters and retains partial coverage.', '',
        '## Exposed validation, 100 original IDs per language', '',
        '| Language | Width | Complete | Median selections | p95 | Singleton bits | Dictionary bytes | Packets bytes |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for language, data in current['languages'].items():
        for width, rec in data['validation'].items():
            s = rec['summary']; q = s['selections']
            lines.append(f'| {language} | {width} | {s["represented"]}/100 | {q["p50"]:g} | {q["p95"]} | {100*s["singleton_fraction"]:.2f}% | {s["dictionary_bytes"]} | {s["packet_bytes"]} |')
    lines += ['', 'Conditional costs for incomplete six-bit rows are not complete-population wins.',
        'The 7/8-bit tables cover every fitting source and every validation source.', '',
        '## Matched 8-bit comparison with the previous mixed macro/spelling protocol', '',
        'Every compared source hash matches the earlier measurement. Both arms cover all 100',
        'validation sources. Pure literal selections are compared with fully charged mixed',
        'payload word-equivalents, not just the mixed opcode count.', '',
        '| Language | Pure median | Mixed median words | Payload change | Complete packet change |',
        '|---|---:|---:|---:|---:|']
    for language, data in current['languages'].items():
        d = comparisons[language]['8']; s = data['validation']['8']['summary']
        old = macro['languages'][language]['validation']['8-mixed']['summary']
        lines.append(f'| {language} | {s["selections"]["p50"]:g} | {old["payload_word_equivalents"]["p50"]:g} | {d["payload_change_percent"]:+.2f}% | {d["packet_change_percent"]:+.2f}% |')
    lines += ['', 'The existing pure-literal format has **41 header bytes**, versus **9** for the',
        'mixed protocol. That real 32-byte difference makes JavaScript pure packets slightly',
        'larger despite lower input bits. Do not describe it as a complete-packet JavaScript win.',
        'Stored dictionary-plus-100-packet packages are 18,096 versus 22,070 bytes for JavaScript,',
        'and 26,167 versus 40,814 for Python. These use their implemented binary versus JSON',
        'dictionary formats; they do not isolate an intrinsic dictionary-storage advantage.',
        f'The pure decoder source closure is {current["decoder_storage_bytes"]:,} bytes, counted separately',
        f'from dictionaries and packets; the mixed decoder reports {macro["decoder_storage_bytes"]["mixed"]:,} bytes.',
        'Including those decoder source files gives 31,110 versus 31,488 bytes for JavaScript',
        'and 39,181 versus 50,232 for Python, across each 100-program package.',
        'Neither count includes the language interpreter/standard library.', '',
        '## Preserved failures and scope', '',
        'The original fit-observed-alphabet run covered only 99/100 JavaScript and 98/100',
        'Python validation sources at 7/8 bits. Its result and packets remain preserved.',
        'The fixed ASCII continuation was motivated by that development failure. It fits only',
        'the 300 fitting sources, but the validation population was already exposed and is',
        'not an untouched confirmation set. The initial pre-validation attempt was stopped',
        'after identifying redundant work; identical alphabet caching and length-indexed',
        'exclusions preserve candidate selection. No validation source was read in that attempt.', '',
        'This does not beat the historical jointly rewritten 8-bit literal frontier of 8,283',
        'validation selections, median 61.5, p95 195 and about 49.5% singleton bits: that used',
        'different source alternatives. The present exact-source arm has 12,306 JavaScript',
        'selections. Neither satisfies M1 median <=32, p95 <=96 or <=10% singleton bits.',
        'No globally optimal vocabulary, unfamiliar-family success or human usability claim.', '',
        '## Evidence and reproduction', '',
        '- [Initial contract](CONTRACT.md), [ASCII continuation](ASCII-CONTINUATION.md).',
        '- [Initial source-free results](results.json), [continuation results](ascii-results.json).',
        '- [Matched comparisons](comparison.json), [initial replay](verification.json), [ASCII replay](ascii-verification.json).',
        '- `test_core.py` and `test_verify.py`: 15 focused tests, including brute-force short',
        '  segmentation, malformed packets and fail-closed population/width checks.',
        '- 45 KnownSpecService/boundary tests passed. Existing pytest judge/lane tests could',
        '  not start because pytest is not installed; no native execution is claimed.',
        '- Exact private tables and packed source are not redistributed. Public reports retain',
        '  original source/receipt identities, table hashes, every arm score and merge trace.', '',
        'Run from Gamma with an explicitly authorized pinned KnownSpecService configuration.',
        'Each output directory must be new and outside Git:', '',
        '```sh',
        'python3 projects/algorithm_solver/literals/pure-literal-compare-v1/test_core.py',
        'python3 projects/algorithm_solver/literals/pure-literal-compare-v1/test_verify.py',
        'python3 projects/algorithm_solver/literals/pure-literal-compare-v1/run.py --service "$CONFIG" --service-sha256 "$SHA" --output "$PRIVATE_INITIAL" --report "$INITIAL_REPORT"',
        'python3 projects/algorithm_solver/literals/pure-literal-compare-v1/ascii_run.py --service "$CONFIG" --service-sha256 "$SHA" --previous "$PRIVATE_INITIAL" --output "$PRIVATE_ASCII" --report "$ASCII_REPORT"',
        'python3 projects/algorithm_solver/literals/pure-literal-compare-v1/verify.py --private "$PRIVATE_ASCII" --output "$VERIFICATION"',
        'python3 projects/algorithm_solver/literals/pure-literal-compare-v1/report.py',
        '```', '']
    (HERE / 'README.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    build()
