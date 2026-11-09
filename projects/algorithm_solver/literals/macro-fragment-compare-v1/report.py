"""Render measured aggregates without selecting or refitting any dictionary."""
import hashlib
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent

def main():
    r=json.loads((HERE/'results.json').read_text())
    if r.get('status')!='completed':raise ValueError('Incomplete comparison')
    lines=['# Matched macro / fragment comparison', '',
           'This measures encoding of existing qualified solutions, not finding solutions from problem descriptions. '
           'All primary-language packets independently reconstruct the exact receipt-bound source bytes. '
           'The 300-fit/100-development-validation partition was reused; validation is exposed development, not fresh confirmation.', '',
           'Dictionary search is heuristic. It does not establish the globally best 64/128/256-entry language. '
           'The mixed arm is a lossless AST-derived source macro DSL with charged operands, not a complete typed semantic compiler.', '',
           'Payload word-equivalents below are total payload bits divided by width. They include spelling and operands; '
           'they are not opcode counts. Packets additionally charge nine framing bytes and byte padding.', '',
           '## Exposed development validation', '',
           '| Language | Width | Representation | Exact-source coverage | Mean words-equivalent | p50 | p95 | Without spelling |',
           '|---|---:|---|---:|---:|---:|---:|---:|']
    labels={'fragment':'Counted fragments','prefix_literal_control':'Prefix literal control','mixed':'Mixed fixed-arity macros'}
    for language,d in r['languages'].items():
        for width in (6,7,8):
            for name,label in labels.items():
                s=d['validation'][f'{width}-{name}']['summary'];m=s['payload_word_equivalents']
                lines.append(f"| {language} | {width} | {label} | {s['represented']}/100 | {m['mean']:.2f} | {m['p50']:.2f} | {m['p95']:.2f} | {s['without_spelling']} |")
    lines+=['','The prefix literal control reserves the same CONCAT code as the mixed arm. '
             'Compare mixed versus that control to isolate the learned macros; compare mixed versus counted fragments for the complete protocol tradeoff.', '',
             '## Paired changes on the same validation problems', '',
             '| Language | Width | Mixed vs counted-fragment bits | Better / equal / worse | Mixed vs prefix-control bits |',
             '|---|---:|---:|---:|---:|']
    for language,d in r['languages'].items():
        for w in (6,7,8):
            maps={name:{x['id']:x for x in d['validation'][f'{w}-{name}']['rows']} for name in labels}
            ids=set.intersection(*(set(m) for m in maps.values()))
            delta=[maps['mixed'][i]['payload_bits']-maps['fragment'][i]['payload_bits'] for i in ids]
            original=sum(maps['fragment'][i]['payload_bits'] for i in ids)
            control=sum(maps['prefix_literal_control'][i]['payload_bits'] for i in ids)
            mixed=sum(maps['mixed'][i]['payload_bits'] for i in ids)
            lines.append(f"| {language} | {w} | {100*(mixed/original-1):+.2f}% | {sum(x<0 for x in delta)} / {sum(x==0 for x in delta)} / {sum(x>0 for x in delta)} | {100*(mixed/control-1):+.2f}% |")
    lines+=['','## Complete packet costs and selection accounting', '',
             'Every packet includes nine framing bytes and byte padding. Primary selections are opcode dispatches; '
             'count words and spelling payload are charged separately. These means all use the same 100 validation sources.', '',
             '| Language | Width | Representation | Mean packet words-equivalent | Packet p50 | Packet p95 | Mean primary selections | Mean count words | Mean spelling bits | Mean closing bits |',
             '|---|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for language,d in r['languages'].items():
        for width in (6,7,8):
            for name,label in labels.items():
                s=d['validation'][f'{width}-{name}']['summary'];m=s['packet_word_equivalents']
                lines.append(f"| {language} | {width} | {label} | {m['mean']:.2f} | {m['p50']:.2f} | {m['p95']:.2f} | {s['primary_selections']['mean']:.2f} | {s['count_words']['mean']:.2f} | {s['spelling_payload_bits']['mean']:.2f} | {s['transition_bits']['mean']:.2f} |")
    lines+=['','## Static compact-Python diagnostic', '',
             'Fit dictionaries were sealed before validation transformation. Unsupported transforms retain original source bytes in the full denominator. '
             'These successor sources have no fresh native qualification: the table is a static representation measurement, not newly qualified coverage.', '',
             '| Width | Representation | Full validation intersection | Mean payload words-equivalent | p50 | p95 | Transformed-only n / mean / p50 / p95 |',
             '|---|---|---:|---:|---:|---:|---|']
    diagnostic=r['languages']['python']['compact_static_diagnostic']
    for w in (6,7,8):
        for name,label in labels.items():
            key=f'{w}-{name}';s=diagnostic['validation'][key]['summary'];m=s['payload_word_equivalents']
            t=diagnostic['validation_transformed_only'][key]['payload_word_equivalents']
            subset=f"{t['n']} / {t['mean']:.2f} / {t['p50']:.2f} / {t['p95']:.2f}" if t else 'none'
            lines.append(f"| {w} | {label} | {s['represented']}/100 | {m['mean']:.2f} | {m['p50']:.2f} | {m['p95']:.2f} | {subset} |")
    transformed=sum(x['status']=='transformed' for x in diagnostic['validation_source_rows'])
    lines+=['',f"Validation transformer: {transformed} transformed; {len(diagnostic['validation_source_rows'])-transformed} original fallbacks. Freshly qualified successors: 0.", '',
             '## Reproduction and limits', '',
             '- [Counting contract](CONTRACT.md); [machine-readable results](results.json).',
             '- `run.py` requires the existing hash-pinned KnownSpecService configuration and an out-of-repository private output directory. It refuses source outside the guarded service.',
             '- Private source files, dictionaries and packets are retained outside Git. Public results bind their source, receipt, table and packet hashes.',
             '- `test_codec.py` checks exhaustive short-string optimal segmentation, nested macro operands, exact integer/Unicode bytes, malformed packets, ownership and AST spans.',
             '- The prerequisite lane checks passed; 27 native judge tests were skipped because this host lacks bubblewrap/prlimit. No candidate was executed without the required sandbox.',
             '- No protected source, model call, training, publication, new native qualification, autonomous solving, or human-fluency result is claimed.',
             '- Whole fit sources/function units/bodies are excluded as table entries. Literals and macro shells must recur in at least two distinct fitting source hashes. Spelling remains an explicit general fallback.',
             '- Decoder and dictionary byte sizes, source membership failures, packet overheads and every fit trial are retained in results.json.', '',
             f"Measured process elapsed: {r['elapsed_seconds']:.3f} seconds. Runtime: {r['runtime']['platform']}. Results SHA-256: `{hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest()}`.", '']
    (HERE/'RESULTS.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
