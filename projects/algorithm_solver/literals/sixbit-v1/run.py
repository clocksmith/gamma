"""Six-bit capacity experiments A, B and C on the matched80 cohort (FREEZE.md).

A: is there a vocabulary of at most 64 entries that exactly segments all 80 programs?
B: how many programs can 64 entries cover (then fewest selections)?
C: literal-escape6-v1 with 63 entries plus ESC: fewest input presses for all 80.
Each job writes its LP certificate (node potentials) and its MILP solution. Nothing
executes candidate source; every packet must decode to a qualified source hash.
"""
import argparse
import hashlib
import importlib.util
import json
import platform
import resource
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import scipy

ROOT = Path(__file__).resolve().parent
LITERALS = ROOT.parent
sys.path[:0] = [str(ROOT), str(LITERALS), str(LITERALS / 'pass2/working')]
import model
import escape6
from literals import dictionary_bytes
from bitpack import encode as ltv_encode

spec = importlib.util.spec_from_file_location('matched80_v1', LITERALS / 'matched80-v1/run.py')
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
sha = lambda b: hashlib.sha256(b).hexdigest()
SCALE = 1 << 20

JOBS = {
    'a-u-compact': ('compact', 'U', 'A'),
    'a-w-compact': ('compact', 'W', 'A'),
    'b-u-compact': ('compact', 'U', 'B'),
    'b-w-compact': ('compact', 'W', 'B'),
    'c-w-compact': ('compact', 'W', 'C'),
    'c-u-compact': ('compact', 'U', 'C'),
    'a-u-canonical': ('canonical', 'U', 'A'),
    'a-w-canonical': ('canonical', 'W', 'A'),
}


def load_contract():
    return json.loads((ROOT / 'contract.json').read_text())


def load_texts(contract, style):
    for rel, digest in contract['inputs'].items():
        if sha((ROOT / rel).read_bytes()) != digest:
            raise ValueError(f'frozen input changed: {rel}')
    texts, rows = v1.load_inputs(json.loads((LITERALS / 'matched80-v1/contract.json').read_text()))
    ids = json.loads((LITERALS / 'matched80-v1/labels/ids.json').read_text())
    if sorted(map(int, texts[style])) != sorted(ids):
        raise ValueError('cohort differs from matched80 ids')
    return texts[style], rows


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def solver_record(res, seconds):
    return {'status': int(res.status), 'message': res.message, 'objective': None if res.x is None else float(res.fun),
            'mip_dual_bound': getattr(res, 'mip_dual_bound', None), 'mip_gap': getattr(res, 'mip_gap', None),
            'mip_node_count': getattr(res, 'mip_node_count', None), 'seconds': round(seconds, 2)}


def distribution(values):
    values = sorted(values)
    if not values:
        return None
    return {'n': len(values), 'total': sum(values), 'min': values[0], 'median': statistics.median(values),
            'p95': values[min(len(values) - 1, int(0.95 * len(values)))], 'max': values[-1]}


def ordered(entries):
    return sorted(entries, key=lambda s: (len(s), s))


def certificate(graph, kind, out, limits, **extra):
    began = time.monotonic()
    res, potentials, mu = model.solve_lp(graph, kind, limits['lp_seconds'], **extra)
    record = {'status': int(res.status), 'message': res.message, 'lp_objective': None if res.status else float(res.fun),
              'seconds': round(time.monotonic() - began, 2)}
    if potentials is not None:
        write(out / 'certificate.json', {'scale': SCALE, 'mu': int(round(mu * SCALE)), 'kind': kind,
                                         'potentials': model.program_potentials(graph, potentials, SCALE)})
    return record


def package(out, texts, rows, style, vocabulary, parses):
    """Canonical LTD1 dictionary and LTV1 six-bit packets for every covered program."""
    entries = ordered(vocabulary)
    if len(entries) > 64:
        return {'six_bit_packets': False, 'reason': f'{len(entries)} entries exceed 64 codes'}
    index = {s: k for k, s in enumerate(entries)}
    dictionary = dictionary_bytes(entries)
    (out / 'dictionary.ltd').write_bytes(dictionary)
    (out / 'packets').mkdir()
    packets = {}
    for p, result in parses.items():
        if result is None:
            continue
        ids = [index[s] for s, _ in result[2]]
        raw = ltv_encode(entries, ids, 6)
        (out / 'packets' / f'{p}.ltv').write_bytes(raw)
        packets[p] = {'selections': len(ids), 'packet_bytes': len(raw), 'packet_sha256': sha(raw),
                      'source_sha256': rows[(int(p), style)]['sha256']}
    total = sum(v['packet_bytes'] for v in packets.values())
    return {'six_bit_packets': True, 'entries': entries, 'dictionary_bytes': len(dictionary),
            'dictionary_sha256': sha(dictionary), 'packet_bytes': total, 'package_bytes': len(dictionary) + total,
            'programs': packets}


def run_job(name, limits):
    style, rule, kind = JOBS[name]
    contract = load_contract()
    out = Path(limits['output']) / name
    out.mkdir(parents=True)
    texts, rows = load_texts(contract, style)
    began = time.monotonic()
    graph = model.Graph(texts, rule, escapes=(kind == 'C'))
    manifest = {'job': name, 'style': style, 'rule': rule, 'experiment': kind, 'model_size': graph.size(),
                'build_seconds': round(time.monotonic() - began, 2)}
    if kind == 'A':
        manifest['lp'] = certificate(graph, 'A', out, limits)
        t = time.monotonic()
        res = model.solve_milp(graph, 'A', limits['milp_seconds'])
        manifest['milp'] = solver_record(res, time.monotonic() - t)
        if res.x is not None:
            shared, parses = model.solution(graph, res)
            used = {s for r in parses.values() if r for s, _ in r[2]}
            manifest['covered'] = sum(r is not None for r in parses.values())
            manifest['entries'] = len(used)
            manifest['private_entries'] = sum(k == 'g' for r in parses.values() if r for _, k in r[2])
            manifest['vocabulary'] = ordered(used)
            manifest['selections'] = {p: r[0] for p, r in parses.items() if r}
            manifest['selection_distribution'] = distribution(list(manifest['selections'].values()))
            manifest['package'] = package(out, texts, rows, style, used, parses)
    elif kind == 'B':
        manifest['lp'] = certificate(graph, 'B1', out, limits, budget=64)
        t = time.monotonic()
        first = model.solve_milp(graph, 'B1', limits['milp_seconds'], budget=64)
        manifest['milp_coverage'] = solver_record(first, time.monotonic() - t)
        if first.x is not None:
            covered = int(round(-first.fun))
            t = time.monotonic()
            second = model.solve_milp(graph, 'B2', limits['second_seconds'], budget=64, min_covered=covered)
            manifest['milp_selections'] = solver_record(second, time.monotonic() - t)
            res = second if second.x is not None else first
            shared, parses = model.solution(graph, res)
            used = {s for r in parses.values() if r for s, _ in r[2]}
            if len(used) > 64:
                raise AssertionError('budget exceeded after reparse')
            manifest['covered'] = sum(r is not None for r in parses.values())
            manifest['covered_programs'] = [p for p in graph.programs if parses[p]]
            manifest['uncovered_programs'] = [p for p in graph.programs if not parses[p]]
            manifest['entries'] = len(used)
            manifest['vocabulary'] = ordered(used)
            manifest['selections'] = {p: r[0] for p, r in parses.items() if r}
            manifest['selection_distribution'] = distribution(list(manifest['selections'].values()))
            manifest['presses'] = 7 * sum(manifest['selections'].values())
            manifest['package'] = package(out, texts, rows, style, used, parses)
    else:
        manifest['lp'] = certificate(graph, 'C', out, limits, budget=63)
        t = time.monotonic()
        res = model.solve_milp(graph, 'C', limits['milp_seconds'], budget=63)
        manifest['milp'] = solver_record(res, time.monotonic() - t)
        if res.x is not None:
            shared, parses = model.solution(graph, res, press=(escape6.SELECTION_PRESSES, escape6.ESCAPE_PRESSES))
            used = {s for r in parses.values() if r for s, k in r[2] if k != 'e'}
            if len(used) > 63:
                raise AssertionError('budget exceeded after reparse')
            entries = ordered(used)
            index = {s: k for k, s in enumerate(entries)}
            dictionary = dictionary_bytes(entries)
            (out / 'dictionary.ltd').write_bytes(dictionary)
            (out / 'packets').mkdir()
            programs = {}
            for p in graph.programs:
                tokens = [('e', s) if k == 'e' else ('d', index[s]) for s, k in parses[p][2]]
                raw = escape6.encode(dictionary, entries, tokens)
                (out / 'packets' / f'{p}.lte').write_bytes(raw)
                escapes = sum(k == 'e' for k, _ in tokens)
                programs[p] = {'tokens': len(tokens), 'selections': len(tokens) - escapes, 'escapes': escapes,
                               'presses': escape6.presses(tokens), 'packet_bytes': len(raw), 'packet_sha256': sha(raw),
                               'source_sha256': rows[(int(p), style)]['sha256']}
                if programs[p]['presses'] != parses[p][0]:
                    raise AssertionError('press accounting mismatch')
            packets = sum(v['packet_bytes'] for v in programs.values())
            manifest.update({
                'codec': escape6.CODEC, 'covered': len(programs), 'entries': len(entries), 'vocabulary': entries,
                'presses': sum(v['presses'] for v in programs.values()),
                'selections': sum(v['selections'] for v in programs.values()),
                'escapes': sum(v['escapes'] for v in programs.values()),
                'escaped_characters': sorted({s for p in graph.programs for s, k in parses[p][2] if k == 'e'}),
                'press_distribution': distribution([v['presses'] for v in programs.values()]),
                'escape_distribution': distribution([v['escapes'] for v in programs.values()]),
                'dictionary_bytes': len(dictionary), 'dictionary_sha256': sha(dictionary), 'packet_bytes': packets,
                'decoder_bytes': escape6.decoder_bytes(),
                'package_bytes_without_decoder': len(dictionary) + packets,
                'package_bytes': escape6.decoder_bytes() + len(dictionary) + packets, 'programs': programs})
    manifest['seconds'] = round(time.monotonic() - began, 2)
    manifest['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    write(out / 'manifest.json', manifest)
    return name, manifest['seconds']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(ROOT / 'run-v1'))
    parser.add_argument('--jobs', nargs='*', default=list(JOBS))
    args = parser.parse_args()
    contract = load_contract()
    out = Path(args.output)
    if out.exists():
        raise SystemExit(f'refusing existing output {out}')
    out.mkdir()
    limits = dict(contract['limits'], output=str(out))
    write(out / 'environment.json', {'python': sys.version, 'scipy': scipy.__version__, 'platform': platform.platform(),
                                     'workers': contract['limits']['workers'], 'jobs': args.jobs})
    with ProcessPoolExecutor(contract['limits']['workers']) as pool:
        for name, seconds in pool.map(run_job, args.jobs, [limits] * len(args.jobs)):
            print(json.dumps({'job': name, 'seconds': seconds}), flush=True)


if __name__ == '__main__':
    main()
