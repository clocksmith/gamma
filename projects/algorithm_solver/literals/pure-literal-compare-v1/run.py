"""Compare actual pure literal packets on the existing 300/100 development split."""
import argparse
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import statistics
import sys
import time

HERE = Path(__file__).resolve().parent
LITERALS = HERE.parent
ROOT = LITERALS.parents[2]
sys.path[:0] = [str(LITERALS), str(LITERALS / 'pass2/working'), str(ROOT)]
import literals
import bitpack
from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
from core import alphabet, pair_fit, sha


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


shapes = module('pure_literal_shapes', LITERALS / 'macro-fragment-compare-v1/shapes.py')


def packed(x):
    return (json.dumps(x, sort_keys=True, indent=2) + '\n').encode()


def write(path, x):
    path.write_bytes(packed(x))


def metrics(values):
    if not values:
        return None
    s = sorted(values)
    return {'n': len(s), 'total': sum(s), 'mean': statistics.mean(s), 'p50': statistics.median(s),
            'p95': s[math.ceil(.95 * len(s)) - 1], 'worst': s[-1]}


def materialize(service, ids, language, folder):
    folder.mkdir()
    sources, members = {}, []
    for pid in ids:
        result = service.request('leetcode:' + str(pid), language=language, include_source=True)
        artifact = result.get('artifact', {})
        impl = result.get('consumer_selection', {}).get('implementation', {})
        if artifact.get('status') != 'materialized':
            members.append({'id': pid, 'status': 'unavailable', 'reason': result.get('reason', result.get('status'))})
            continue
        text = artifact['source_utf8']
        if impl['status'] != 'qualified' or sha(text.encode()) != impl['source_sha256']:
            raise ValueError('Source qualification binding')
        if len(text.encode()) > 65536:
            members.append({'id': pid, 'status': 'source-limit'})
            continue
        sources[str(pid)] = text
        (folder / (str(pid) + '.source')).write_bytes(text.encode())
        members.append({'id': pid, 'status': 'available', **{k: impl[k] for k in
            ['source_sha256', 'receipt_sha256', 'runtime_sha256', 'tests_sha256', 'contract_scope', 'caveats']}})
    return sources, members


def evaluate(sources, dictionary, width, population, folder=None):
    data = literals.dictionary_bytes(dictionary)
    rows, uses = [], Counter()
    if folder:
        folder.mkdir()
        (folder / 'dictionary.ltd').write_bytes(data)
        write(folder / 'dictionary.json', dictionary)
    for pid, source in sources.items():
        row = {'id': int(pid), 'source_sha256': sha(source.encode())}
        try:
            seq = literals.shortest_encode(source, dictionary)
        except ValueError:
            rows.append({**row, 'status': 'uncovered'})
            continue
        packet = bitpack.encode(dictionary, seq, width)
        if bitpack.decode(data, packet) != source:
            raise ValueError('Independent packet reconstruction differs')
        singleton = sum(len(dictionary[i]) == 1 for i in seq)
        uses.update(seq)
        rows.append({**row, 'status': 'represented', 'selections': len(seq),
            'payload_bits': width * len(seq), 'singleton_bits': width * singleton,
            'packet_bytes': len(packet), 'padding_bits': (-width * len(seq)) % 8,
            'packet_sha256': sha(packet)})
        if folder:
            (folder / (pid + '.ltv')).write_bytes(packet)
    covered = [r for r in rows if r['status'] == 'represented']
    payload = sum(r['payload_bits'] for r in covered)
    singleton = sum(r['singleton_bits'] for r in covered)
    summary = {'population': population, 'available': len(sources), 'represented': len(covered),
        'uncovered': len(sources) - len(covered), 'unavailable': population - len(sources),
        'dictionary_entries': len(dictionary), 'used_entries': len(uses),
        'dictionary_bytes': len(data), 'dictionary_sha256': sha(data),
        'selections': metrics([r['selections'] for r in covered]),
        'payload_bits': payload, 'singleton_bits': singleton,
        'singleton_fraction': singleton / payload if payload else None,
        'packet_bytes': sum(r['packet_bytes'] for r in covered),
        'framing_bytes_per_packet': 41,
        'dictionary_plus_packets_bytes': len(data) + sum(r['packet_bytes'] for r in covered)}
    return {'summary': summary, 'rows': rows}


def fit(sources, language):
    if not sources:
        raise ValueError('No qualified fitting sources available; language blocked before fitting')
    metadata, errors = shapes.shapes(sources, language)
    if errors:
        raise ValueError('AST exclusions unavailable for fitting sources')
    banned = {s.encode().strip() for s in sources.values()}
    for pid, s in sources.items():
        raw = s.encode()
        banned.update(raw[a:b].strip() for a, b in metadata[pid]['banned'])
    tables, reports, traces = {}, {}, {}
    for width in [6, 7, 8]:
        cap = 1 << width
        chars, freq = alphabet(sources, cap)
        trials = [('frequency_characters', freq, []), ('coverage_characters', chars, [])]
        cache = {}
        for reserve in [0, 8, 16]:
            initial, _ = alphabet(sources, cap - reserve)
            key = tuple(initial)
            if key not in cache:
                cache[key] = pair_fit(sources, initial, cap, banned)
            dictionary, trace = cache[key]
            trials.append(('pairs_reserve_' + str(reserve), dictionary, trace))
        evaluated = []
        for name, dictionary, trace in trials:
            result = evaluate(sources, dictionary, width, 300)
            score = result['summary']
            evaluated.append((name, dictionary, result))
            traces[str(width) + '-' + name] = {'summary': score, 'merges': trace}
        # Coverage first; no cost comparison of incomplete arms as complete ones.
        chosen = min(evaluated, key=lambda r: (-r[2]['summary']['represented'],
            (r[2]['summary']['selections'] or {'total': 0})['total'],
            r[2]['summary']['dictionary_bytes'], r[0]))
        name, dictionary, result = chosen
        tables[str(width)] = dictionary
        reports[str(width)] = {'method': name, **result}
        print(language, width, name, result['summary'], flush=True)
    return tables, reports, traces


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--service', type=Path, required=True)
    parser.add_argument('--service-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(ROOT):
        raise ValueError('Private sources/tables/packets must stay outside Git')
    args.output.mkdir(parents=True, exist_ok=False)
    service = KnownSpecService.from_config(args.service.resolve(), args.service_sha256)
    split_path = LITERALS / 'cost-decomposition-v1/contract.json'
    if sha(split_path.read_bytes()) != 'a2c501792e4ef369a1f2630fd4ffd3b6623c1146ca3d7aac7115b469efe8cd61':
        raise ValueError('Original development partition hash differs')
    split = json.loads(split_path.read_bytes())['partition']
    fitids, validids = split['dev_fit'], split['dev_val']
    if len(fitids) != len(set(fitids)) or len(validids) != len(set(validids)) or len(fitids) != 300 or len(validids) != 100 or set(fitids) & set(validids):
        raise ValueError('Original development partition changed')
    code = [HERE / 'core.py', HERE / 'run.py', LITERALS / 'literals.py',
        LITERALS / 'pass2/working/bitpack.py', LITERALS / 'macro-fragment-compare-v1/shapes.py',
        LITERALS / 'macro-fragment-compare-v1/js_shapes.cjs']
    contract = {'partition_sha256': sha(split_path.read_bytes()), 'service_sha256': args.service_sha256,
        'widths': [6, 7, 8], 'fit_ids': fitids, 'validation_ids': validids,
        'code_pins': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in code},
        'source_execution': False, 'source_publication': False, 'validation_fit': False,
        'controls': 'Frequency and coverage characters; pair merges with 0/8/16 reserved slots.'}
    write(args.output / 'contract.json', contract)
    report = {'schema': 'gamma.pure-literal-development.v1', 'contract': contract, 'languages': {},
        'decoder_storage_bytes': sum(p.stat().st_size for p in code[2:4]),
        'limits': ['Exact reconstruction of qualified bytes, not autonomous solving.',
            'The 100 validation programs are exposed development, not held-out evidence.',
            'No macros, spelling escape, free names, implicit helpers or new native qualification.',
            'Incomplete coverage retains the original denominator; cost quantiles are conditional.',
            'Heuristic search and finite development evidence, not optimality or M1 qualification.']}
    start = time.monotonic()
    for language in ['javascript', 'python']:
        folder = args.output / language
        folder.mkdir()
        sources, membership = materialize(service, fitids, language, folder / 'fit')
        tables, fits, trials = fit(sources, language)
        write(folder / 'sealed-tables.json', tables)
        seal = sha((folder / 'sealed-tables.json').read_bytes())
        valid, validmembership = materialize(service, validids, language, folder / 'validation')
        vals = {width: evaluate(valid, d, int(width), 100, folder / ('validation-' + width))
            for width, d in tables.items()}
        for width, dictionary in tables.items():
            receipt = evaluate(sources, dictionary, int(width), 300, folder / ('fit-' + width))
            if receipt != {k: v for k, v in fits[width].items() if k != 'method'}:
                raise ValueError('Sealed fitting receipt differs')
        report['languages'][language] = {'fit_membership': membership, 'validation_membership': validmembership,
            'fit': fits, 'validation': vals, 'trials': trials, 'seal_sha256': seal}
        print(language, 'validation', {w: r['summary'] for w, r in vals.items()}, flush=True)
    report['elapsed_seconds'] = time.monotonic() - start
    write(args.report, report)
    write(args.output / 'results.json', report)


if __name__ == '__main__':
    main()
