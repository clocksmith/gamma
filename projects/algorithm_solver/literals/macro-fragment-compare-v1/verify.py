"""Replay sealed packets and independently recompute costs; never refit or execute sources."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

import codec
import run
import shapes


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def metric(values):
    if not values:
        return None
    ordered = sorted(values)
    return dict(n=len(values), mean=statistics.mean(values), p50=statistics.median(values),
                p95=ordered[math.ceil(.95 * len(values)) - 1], worst=max(values), total=sum(values))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--private', type=Path, required=True)
    parser.add_argument('--results', type=Path, default=run.HERE / 'results.json')
    parser.add_argument('--output', type=Path, default=run.HERE / 'verification.json')
    args = parser.parse_args()
    result = json.loads(args.results.read_bytes())
    assert result['status'] == 'completed'
    contract = (args.private / 'run-contract.json').read_bytes()
    assert digest(contract) == result['contract_sha256']
    checked = 0
    table_count = 0
    summaries = 0
    for language, data in result['languages'].items():
        folder = args.private / language
        source_sets = {}
        for split in ('fit', 'validation'):
            sources = {str(row['id']): (folder / split / (str(row['id']) + '.source')).read_text()
                       for row in data[split + '_membership'] if row['status'] == 'available'}
            assert len(data[split + '_membership']) == data[split + '_population']
            for row in data[split + '_membership']:
                if row['status'] == 'available':
                    assert digest(sources[str(row['id'])].encode()) == row['source_sha256']
            source_sets[split] = sources
        metadata, _ = shapes.shapes(source_sets['fit'], language)
        literals, macros, _, original_banned, support = shapes.mine(source_sets['fit'], metadata)
        populations = [(folder, data, source_sets, literals, macros, support)]
        if language == 'python':
            diagnostic = data['compact_static_diagnostic']
            assert diagnostic['qualified_successors'] == 0
            compact = {}
            for split, sources in source_sets.items():
                compact[split] = {}
                records = {str(row['id']): row for row in diagnostic[split + '_source_rows']}
                assert records.keys() == sources.keys()
                for pid, source in sources.items():
                    if records[pid]['status'] == 'transformed':
                        candidate, _ = run.TRANSFORM.transform(source)
                        assert digest(candidate.encode()) == records[pid]['candidate_sha256']
                    else:
                        candidate = source
                    compact[split][pid] = candidate
            metadata, _ = shapes.shapes(compact['fit'], 'python')
            literals, macros, _, _, support = shapes.mine(compact['fit'], metadata, original_banned)
            populations.append((folder / 'compact-static', diagnostic, compact, literals, macros, support))
        for location, population, sources, literals, macros, support in populations:
            seal_bytes = (location / 'sealed-tables.json').read_bytes()
            assert digest(seal_bytes) == population['seal_sha256']
            tables = json.loads(seal_bytes)
            allowed_literals, allowed_macros = set(literals), set(macros)
            for width_text, arms in tables.items():
                width = int(width_text)
                assert arms['prefix_literal_control'] == arms['fragment'][:-1]
                for arm, entries in arms.items():
                    table = tuple(tuple(part.encode() for part in entry) for entry in entries)
                    assert len(table) == (1 << width) - (1 if arm == 'fragment' else 2)
                    assert len(set(table)) == len(table)
                    for parts in table:
                        key = parts[0] if len(parts) == 1 else parts
                        assert key in (allowed_literals if len(parts) == 1 else allowed_macros)
                        assert support[key] >= 2
                    table_count += 1
                    for split in ('fit', 'validation'):
                        report = population[split][f'{width}-{arm}']
                        rows = report['rows']
                        assert {str(row['id']) for row in rows} == sources[split].keys()
                        assert len(rows) == len({row['id'] for row in rows})
                        assert digest(run.packed(entries)) == report['summary']['dictionary_sha256']
                        for row in rows:
                            binary = (location / f'{split}-{width}-{arm}' / f"{row['id']}.bin").read_bytes()
                            assert digest(binary) == row['packet_sha256']
                            if arm == 'fragment':
                                decoded = run.FSP.decode_packet(binary, [parts[0].decode() for parts in table], width).encode()
                            else:
                                decoded, stats = codec.unpack(binary, table, width)
                                for key, value in stats.items():
                                    if key != 'entry_uses':
                                        assert row[key] == value
                            assert decoded == sources[split][str(row['id'])].encode()
                            assert digest(decoded) == row['source_sha256']
                            bits = int.from_bytes(binary[5:9], 'big')
                            assert bits == row['payload_bits']
                            assert len(binary) * 8 == row['packet_bits'] == bits + 72 + row['padding_bits']
                            assert bits == width * row['primary_selections'] + row['spelling_payload_bits'] + row['transition_bits'] + row['concat_count_bits']
                            assert row['count_words'] * width == row['concat_count_bits']
                            assert row['payload_word_equivalents'] == bits / width
                            assert row['packet_word_equivalents'] == len(binary) * 8 / width
                            checked += 1
                        for key, value in report['summary'].items():
                            if isinstance(value, dict) and 'mean' in value:
                                assert value == metric([row[key] for row in rows])
                                summaries += 1
                        assert report['summary']['represented'] == len(rows)
                        assert report['summary']['without_spelling'] == sum(row['spelled_bytes'] == 0 for row in rows)
                trials = population['trials'][width_text]['macro_trials']
                score = sum(row['packet_bits'] for row in population['fit'][f'{width}-prefix_literal_control']['rows'])
                for trial in trials:
                    assert trial['fit_bits_before'] == score
                    assert trial['accepted'] == (trial['fit_bits_candidate'] < score)
                    assert trial['support'] >= 2
                    if trial['accepted']:
                        score = trial['fit_bits_candidate']
                assert score == sum(row['packet_bits'] for row in population['fit'][f'{width}-mixed']['rows'])
            if location.name == 'compact-static':
                ids = {row['id'] for row in population['validation_source_rows'] if row['status'] == 'transformed'}
                for key, report in population['validation'].items():
                    values = [row['payload_word_equivalents'] for row in report['rows'] if row['id'] in ids]
                    assert population['validation_transformed_only'][key] == dict(n=len(values), payload_word_equivalents=metric(values))
    receipt = dict(status='passed', results_sha256=digest(args.results.read_bytes()),
                   verifier_sha256=digest(Path(__file__).read_bytes()), packets_checked=checked,
                   tables_checked=table_count, aggregate_metrics_recomputed=summaries,
                   native_execution=False, source_publication=False)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
