"""Produce timing-only reports after the locked 96-table confirmation has finished."""

from argparse import ArgumentParser
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import time
from table_costs import RIVALS, report

HERE = Path(__file__).resolve().parent
LOCK_HASH = '3034436e29a2f878eaed0d39d900653913d73016727fead590c6d58bc3e7511f'
TOKENIZER_HASH = '9adedd6e3eea57c67a8b924d5c511f8cbb30d53cf9794978a9baef39e23f5e98'


def require(expr, msg):
    if not expr:
        raise ValueError(msg)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def layout(n, seed):
    return {
        f'confirm-{start:02d}-{start + 4:02d}.json': {
            f'confirm_{seed}_s{i}_{"word" if i < n // 2 else "pair"}': (i, set(range(i * 16, (i + 1) * 16)))
            for i in range(start, start + 4)
        }
        for start in range(0, n, 4)
    }


def interval(v):
    if v is None:
        return 'never'
    if v['last'] is None:
        return 'all' if v['first'] == 1 else f'≥{v["first"]}'
    if v['first'] == v['last']:
        return str(v['last'])
    return f'{v["first"]}–{v["last"]}'


def markdown(data):
    def line(label, entry):
        vals = []
        for a in RIVALS:
            c = entry['comparisons'][a]
            vals.extend(
                interval(c[k])
                for k in ('adapterAtLeastAsFastAtQueryCounts', 'otherAtLeastAsFastAtQueryCounts')
            )
        return '| ' + ' | '.join([label, *vals]) + ' |'

    header = [
        '| Measured mix | Adapter ≤ KV | KV ≤ adapter | Adapter ≤ classifier | Classifier ≤ adapter |',
        '| --- | ---: | ---: | ---: | ---: |',
    ]
    text = [
        '# MiniCPM4 time to recover setup cost',
        '',
        'The primary report includes all 96 tables. Counts are positive integers. Each cell gives the query counts where the named method is at least as fast including setup; an exact tie can appear in both columns.',
        '',
        '## Equal-weighted tables',
        '',
        *header,
    ]
    for name, c in data['cohorts'].items():
        text.append(line(f'{name} ({c["tables"]} tables, {c["observedQuestions"]} questions)', c))
    text.extend(
        [
            '',
            'Each cohort estimates the cost of one uniformly selected table followed by N queries from the indicated answer mix. The observed timings include the classifier’s query feature extraction and the warm cache restore. The candidate setup includes shared feature capture plus fitting and upload.',
            '',
            'Word-only codes can occupy multiple tokenizer tokens. The target-length cohorts count tokens after the same answer marker as the runner. A two-part color and digit code is one lexical category.',
            '',
            '## Individual tables',
            '',
            *header,
        ]
    )
    for name, e in sorted(data['tables'].items(), key=lambda x: int(x[0].split('_s')[-1].split('_')[0])):
        text.append(
            line(name + (' (concurrent work reported)' if e['reportedBuildOverlapPossible'] or e.get('additionalWorkOverlapPossible') else ''), e)
        )
    text.extend(
        [
            '',
            'The original timing sensitivity excludes the first four tables for the 02:48–03:02 UTC build. The primary comparison retains every table.',
            *[f"Additional reported work ran from {event['startUtc']} to {event['endUtc']} during table range {event['tableRange']}." for event in data['timingEvidence'].get('additionalConcurrentWork', [])],
            'Where additional overlaps were recorded, outsideAllReportedWork omits every reported range. Individual question wall-clock timestamps are unavailable; other load may have occurred.',
            '',
        ]
    )
    return '\n'.join(text)


def finalize(study, dest):
    require(
        (study / 'DONE').is_file() and not (study / 'BLOCKED').exists(),
        'Study must have DONE and no BLOCKED marker',
    )
    published = dest / 'confirmation'
    inputs = study / 'source/projects/reconfiguration/query_swiglu_fastweight_v5'
    lock = inputs / 'minicpm4_confirmation_lock.json'
    require(digest(lock) == LOCK_HASH, 'Unexpected frozen comparison')
    l = json.loads(lock.read_text())
    summary_file = study / 'confirmed-summary.json'
    summary = json.loads(summary_file.read_text())
    require(
        summary['lock_sha256'] == LOCK_HASH
        and summary['valid_controls'] is True
        and (summary['tables'], summary['questions']) == (96, 1536),
        'Incomplete or invalid result',
    )
    planned = layout(96, l['confirm']['seed'])
    expected = summary['receipt_sha256']
    require(
        set(planned) == set(expected) == {p.name for p in study.glob('confirm-*.json')},
        'Missing or unexpected range receipts',
    )
    ledger_file = study / 'receipt-digests.sha256'
    ledger = {}
    for line in ledger_file.read_text().splitlines():
        h, n = line.split('  ', 1)
        require(n not in ledger, 'Duplicate item in study digest ledger')
        ledger[n] = h
    require(ledger.get(summary_file.name) == digest(summary_file), 'Summary digest mismatch')
    for n, h in expected.items():
        require(ledger.get(n) == h == digest(study / n), 'Receipt digest mismatch for ' + n)
    prov_file = study / 'timing-provenance.json'
    prov = json.loads(prov_file.read_text())
    overlap = prov['overlapping_confirm_range']
    require(
        overlap == [0, 4]
        and prov['reported_concurrent_build_utc'] == ['2026-11-20T02:48:00Z', '2026-11-20T03:02:00Z'],
        'Unexpected timing-provenance record',
    )
    additional_ranges = [event['tableRange'] for event in prov.get('additionalConcurrentWork', [])]
    for start, stop in additional_ranges:
        require(type(start) is int and type(stop) is int and 0 <= start < stop <= 96,
                'Invalid additional timing range')
    tasks = inputs / 'tasks_v5.py'
    require(digest(tasks) == l['source_sha256']['tasks_v5.py'], 'Task vocabulary changed')
    defs = runpy.run_path(str(tasks))
    codes = [*defs['WORD_CODES'], *(f'{w}-{i}' for w in defs['PAIR_WORDS'] for i in range(1, 10))]
    tokenizer = study.parent / 'models' / l['model']['id'] / 'tokenizer.json'
    require(digest(tokenizer) == TOKENIZER_HASH, 'Tokenizer identity changed')
    engine = study / 'engine'
    require(
        subprocess.check_output(['git', '-C', str(engine), 'rev-parse', 'HEAD'], text=True).strip()
        == l['engine']
        and not subprocess.check_output(
            ['git', '-C', str(engine), 'status', '--porcelain', '--', 'src']
        ).strip(),
        'Pinned tokenizer engine differs from the lock',
    )
    helper = HERE / 'minicpm4_cost_tokens.mjs'
    lengths = json.loads(
        subprocess.check_output(
            ['node', str(helper), str(engine), str(tokenizer)], input=json.dumps(codes), text=True
        )
    )
    require(
        set(lengths) == set(codes) and all(type(v) is int and v > 0 for v in lengths.values()),
        'Incomplete tokenizer mapping',
    )
    source_hashes = {p.name: digest(p) for p in [Path(__file__).resolve(), HERE / 'table_costs.py', helper]}
    provenance = {
        'studySummarySha256': digest(summary_file),
        'studyLockSha256': LOCK_HASH,
        'timingEvidenceSha256': digest(prov_file),
        'tokenizerSha256': TOKENIZER_HASH,
        'reportSourcesSha256': source_hashes,
        'rawReceiptSha256': expected,
    }
    if published.exists():
        prior = json.loads((published / 'costs.json').read_text())
        require(prior['inputDigests'] == provenance, 'Existing cost report belongs to different inputs')
        hashes = json.loads((published / 'report-digests.json').read_text())
        require(
            set(hashes) == {'costs.json', 'TABLE_COSTS.md'}
            and all(digest(published / name) == h for name, h in hashes.items()),
            'Existing cost report checksum mismatch',
        )
        return published
    out = report(
        [study / n for n in sorted(planned)], token_lengths=lengths, layout=planned, overlap=overlap,
        additional_work_ranges=additional_ranges,
    )
    for name, t in out['tables'].items():
        require(
            t['codeShape'] == ('twoPartCode' if name.endswith('_pair') else 'wordCode'),
            'Mislabeled code shape ' + name,
        )
    require(
        out['cohorts']['allTables']['observedQuestions'] == 1536
        and len(out['tables']) == 96
        and out['cohorts']['reportedOverlapRange']['tables'] == 4
        and out['cohorts']['outsideReportedOverlapRange']['tables'] == 92,
        'Timing strata do not cover the locked design',
    )
    if additional_ranges:
        excluded = set(range(*overlap))
        for start, stop in additional_ranges:
            excluded.update(range(start, stop))
        included = out['cohorts'].get('outsideAllReportedWork', {})
        require(included.get('tables', 0) == 96 - len(excluded), 'Incomplete combined timing sensitivity')
    out.update(
        {
            'reportVersion': 2,
            'inputDigests': provenance,
            'timingEvidence': prov,
            'expectedAnswerTokens': lengths,
        }
    )
    dest.mkdir(exist_ok=True, parents=True)
    tmp = Path(tempfile.mkdtemp(dir=dest, prefix='.confirm-costs-'))
    try:
        (tmp / 'costs.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
        (tmp / 'TABLE_COSTS.md').write_text(markdown(out))
        (tmp / 'report-digests.json').write_text(
            json.dumps({n: digest(tmp / n) for n in ('costs.json', 'TABLE_COSTS.md')}, indent=2) + '\n'
        )
        os.rename(tmp, published)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    return published


def main():
    ap = ArgumentParser(description=__doc__)
    ap.add_argument('study', type=Path)
    ap.add_argument('destination', type=Path)
    ap.add_argument('--wait', action='store_true', help='Wait for the DONE marker and exit after one report')
    args = ap.parse_args()
    while not (args.study / 'DONE').exists():
        if (args.study / 'BLOCKED').exists():
            print('Study blocked before completion. No final timing report generated.')
            return
        if not args.wait:
            ap.exit(2, 'Waiting for DONE. No confirmation receipts were opened.\n')
        time.sleep(60)
    try:
        published = finalize(args.study, args.destination)
    except Exception as exc:
        if not args.wait:
            raise
        args.destination.mkdir(exist_ok=True, parents=True)
        (args.destination / 'report-error.txt').write_text(f'{type(exc).__name__}: {exc}\n')
        print('Final report stopped: ' + str(exc), flush=True)
        return
    print(published)


if __name__ == '__main__':
    main()
