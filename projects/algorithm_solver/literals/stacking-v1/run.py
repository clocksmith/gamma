"""Eight fit-only stack outputs, sealed validation, exact decoding and final parity.

This entry point performs no structured-codec sidecar. Use an external process
wall guard from the execution freeze; this file never grants its own launch.
"""
import argparse
import concurrent.futures
import json
import multiprocessing
import os
from pathlib import Path
import platform
import resource
import sys
import time
import engine as e

HERE, LIT, analyze = e.HERE, e.LIT, e.analyze
POLICIES = ('canonical', 'shortest_min_char')


def read(path):
    return e.read(path)

def write_atomic(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    temporary.replace(path)

def status(out, phase, complete=False):
    write_atomic(out/'status.json', {'phase': phase, 'complete': complete})


def verify_fit(folder):
    seal = read(folder/'fit-seal.json')
    assert seal['validation_loaded'] is False
    for name, digest in seal['files'].items():
        assert analyze.sha((folder/name).read_bytes()) == digest, (folder, name)


def parallel(function, jobs, workers=4):
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers,
            mp_context=multiprocessing.get_context('spawn')) as pool:
        return list(pool.map(function, jobs))


def measure(arm, sources, vocab, banned, out, c):
    """Actual selected entries only, with no fallback restoration or dropped failures."""
    assert len(vocab) == len(set(vocab)) <= 256
    folder = out/'artifacts'/arm
    folder.mkdir(parents=True)
    analyze.write(folder/'sources.json', sources)
    analyze.write(folder/'dictionary.json', vocab)
    db = analyze.dictionary_bytes(vocab)
    (folder/'dictionary.bin').write_bytes(db)
    illegal = sorted(analyze.sha(s.encode()) for s in set(vocab) & banned)
    results = []
    for policy in POLICIES:
        packets = folder/policy
        packets.mkdir()
        rows = {}
        for pid, text in sorted(sources.items()):
            row = {'source_sha256': analyze.sha(text.encode()), 'source_bytes': len(text.encode())}
            try:
                seq = e.segment.encode(text, vocab, policy)
            except ValueError:
                rows[pid] = {**row, 'encodable': False}
                continue
            if policy == 'canonical':
                assert seq == analyze.shortest_encode(text, vocab)
            packet = analyze.encode(vocab, seq, 8)
            assert analyze.decode(db, packet) == text
            (packets/f'{pid}.bin').write_bytes(packet)
            rows[pid] = {**row, 'encodable': True, 'selections': len(seq), 'actions': len(seq)+1,
                         'single_characters': sum(len(vocab[i]) == 1 for i in seq),
                         'packet_bytes': len(packet), 'packet_sha256': analyze.sha(packet),
                         'one_program_package_bytes': len(db)+len(packet)}
        a = {'arm': arm, 'policy': policy, 'width': 8, 'entries': len(vocab),
             'character_entries': sum(len(s) == 1 for s in vocab), 'dictionary_bytes': len(db),
             'dictionary_sha256': analyze.sha((folder/'dictionary.json').read_bytes()),
             'dictionary_binary_sha256': analyze.sha(db), 'per_problem': rows,
             'illegal_entry_sha256': illegal}
        for split, key in (('fit', 'dev_fit'), ('validation', 'dev_val')):
            ids = c['partition'][key]
            d = e.tail.aggregate(rows, ids, len(db))
            good = [rows[str(pid)] for pid in ids if rows[str(pid)]['encodable']]
            d.update(single_character_codes=sum(r['single_characters'] for r in good),
                     source_bytes=sum(rows[str(pid)]['source_bytes'] for pid in ids),
                     framing_bytes=41*len(good), padding_bits=0,
                     payload_bits=8*sum(r['selections'] for r in good),
                     package_with_decoder_dependencies=d['package_bytes']+c['decoder_dependency_bytes'])
            a[split] = d
        results.append(a)
    canonical, minimum = results
    for pid, row in canonical['per_problem'].items():
        other = minimum['per_problem'][pid]
        assert row['encodable'] == other['encodable']
        if row['encodable']:
            assert row['selections'] == other['selections']
            assert other['single_characters'] <= row['single_characters']
    return results


def parity_job(job):
    work, pid, text, spec, cores = job
    os.sched_setaffinity(0, set(cores))
    minify = e.module('stack_parity_minify', LIT/'minify-control-v1/minify.py')
    return minify.style.parity(minify.shim(Path(work)), pid, text, 'solve', spec, None)


def qualify(work, out, c, arms):
    # Only these two declared receipt sources qualify unchanged hashes. Item23's
    # failed later run remains recorded; there is no retry or replacement here.
    known = {}
    receipts = read(LIT/'binding-descent-v1/evidence/results.json')['arms']
    control = next(a for a in receipts if a['arm'] == 'control' and a['width'] == 8)
    seed = next(a for a in read(LIT/'lns-naming-v1/evidence/results.json')['arms']
                if a['arm'] == 'seed_fixed_seed')
    for name, arm in (('item13_R', control), ('item15_seed', seed)):
        for pid, row in arm['per_problem'].items():
            q = arm['qualification'][pid]
            assert q['passed']
            known[(pid, row['source_sha256'])] = {'passed': True, 'reused': True,
                                                'receipt_source': name}
    allowed = {str(x['id']) for x in c['qualification']}
    manifest = read(work/'population500/manifest.json')
    specs = {int(r['id']): r for r in manifest['rows'] if str(r['id']) in allowed}
    assert set(specs) == {int(i) for i in allowed}
    jobs = {}
    for arm in arms:
        sources = read(out/'artifacts'/arm['arm']/'sources.json')
        for pid, row in arm['per_problem'].items():
            key = (pid, row['source_sha256'])
            if key not in known:
                jobs[key] = sources[pid]
    fresh, failures = {}, {}
    write_atomic(out/'qualification-private.json', {'receipts': fresh, 'failures': failures})
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,
            mp_context=multiprocessing.get_context('spawn')) as pool:
        pending = {pool.submit(parity_job, (str(work), int(pid), text, specs[int(pid)], c['all_cores'])): (pid, h)
                   for (pid, h), text in jobs.items()}
        for future in concurrent.futures.as_completed(pending):
            pid, digest = pending[future]
            key = f'{pid}:{digest}'
            passed, ok, total, bad = future.result()
            fresh[key] = {'passed': passed, 'checks_passed': ok, 'cases': total, 'reused': False}
            if bad:
                failures[key] = bad
            write_atomic(out/'qualification-private.json', {'receipts': fresh, 'failures': failures})
    for arm in arms:
        arm['qualification'] = {}
        for pid, row in arm['per_problem'].items():
            key = (pid, row['source_sha256'])
            q = known[key] if key in known else fresh[f'{pid}:{key[1]}']
            arm['qualification'][pid] = q
            row['qualified_source'] = q['passed']
        for split, group in (('fit', 'dev_fit'), ('validation', 'dev_val')):
            arm[split]['qualified'] = sum(arm['qualification'][str(i)]['passed'] and
                arm['per_problem'][str(i)]['encodable'] for i in c['partition'][group])
    return {'distinct_new_sources': len(fresh), 'passed': sum(q['passed'] for q in fresh.values()),
            'checks_passed': sum(q['checks_passed'] for q in fresh.values()),
            'checks': sum(q['cases'] for q in fresh.values()), 'failed_sources': len(failures)}


def main(work, out):
    c = read(HERE/'contract.json')
    assert c['execution_status'] == 'requires_pushed_freeze_and_cross_review'
    import numpy, scipy
    assert Path(sys.executable).absolute() == Path(c['python_bin']).absolute()
    assert c['versions'] == {'python': platform.python_version(), 'numpy': numpy.__version__, 'scipy': scipy.__version__}
    assert os.environ.get('OMP_NUM_THREADS') == os.environ.get('OPENBLAS_NUM_THREADS') == '1'
    os.sched_setaffinity(0, set(c['all_cores']))
    resource.setrlimit(resource.RLIMIT_AS, (c['limits']['address_space_bytes'], c['limits']['address_space_bytes']))
    for rel, digest in c['code_hashes'].items():
        assert analyze.sha((LIT/rel).read_bytes()) == digest, rel
    for path, digest in c['runtime_files'].items():
        assert analyze.sha(Path(path).read_bytes()) == digest, path
    for rel, digest in c['private_files'].items():
        assert analyze.sha((work/rel).read_bytes()) == digest, rel
    for q in c['qualification']:
        for rel, digest in q['files'].items():
            assert analyze.sha((work/rel).read_bytes()) == digest, rel
    assert analyze.sha((work/'population500/manifest.json').read_bytes()) == c['manifest_sha256']
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    source_jobs = [(arm, str(work), str(out), c, cores)
                   for arm, cores in zip(e.SOURCE_ARMS, c['source_cores'])]
    status(out, 'source_fit')
    summaries = parallel(e.fit_source, source_jobs)
    for arm in e.SOURCE_ARMS:
        verify_fit(out/'fit'/arm)
    status(out, 'repair')
    repairs = parallel(e.repair_trajectory,
                       [(mode, str(out), c, cores) for mode, cores in
                        zip(('fixed96', 'optional'), c['repair_cores'])], workers=2)
    status(out, 'weighted_finish')
    summaries += parallel(e.finish_dictionary, [(arm, str(out), c, cores)
                         for arm, cores in zip(e.DEEP_ARMS, c['source_cores'])])
    for arm in (*e.SOURCE_ARMS, *e.DEEP_ARMS):
        verify_fit(out/'fit'/arm)
    analyze.write(out/'all-fit-sealed.json', {'validation_loaded': False, 'arms': summaries, 'repairs': repairs})
    status(out, 'validation')
    val = parallel(e.validation_sources, source_jobs)
    analyze.write(out/'all-validation-sealed.json', {'qualification_started': False, 'arms': val})
    refs = {}
    for arm in ('R', 'seed13'):
        root = work/c['references'][arm]
        refs[arm] = (read(root/'sources.json'), read(root/'dictionary.json'))
    refs['best24'] = (refs['seed13'][0], read(work/c['references']['best24']/'dictionary.json'))
    expected = {str(i) for ids in c['partition'].values() for i in ids}
    results = []
    for arm, (sources, vocab) in refs.items():
        assert set(sources) == expected
        results += measure(arm, sources, vocab, e.base.sel.forbidden_strings(sources), out, c)
    for arm in (*e.SOURCE_ARMS, *e.DEEP_ARMS):
        folder = out/'fit'/arm
        source_arm = arm if arm in e.SOURCE_ARMS else 'NCP'
        valroot = out/'fit'/source_arm
        sources = {**read(folder/'fit-sources.json'), **read(valroot/'validation-sources.json')}
        assert set(sources) == expected
        vocab = read(folder/'dictionary.json')
        banned = set(read(folder/'fit-banned.json')) | set(read(valroot/'all-banned.json'))
        results += measure(arm, sources, vocab, banned, out, c)
    analyze.write(out/'unqualified-results.json', results)
    print('[qualification] all outputs sealed; four workers; no retries or replacements', flush=True)
    status(out, 'qualification')
    fresh = qualify(work, out, c, results)
    result = {'arms': results, 'fit_summaries': summaries, 'repair_summaries': repairs,
              'fresh_qualification_summary': fresh, 'seconds': time.monotonic()-start,
              'contract_sha256': analyze.sha((HERE/'contract.json').read_bytes()),
              'decoded_packets': sum(a['fit']['covered']+a['validation']['covered'] for a in results)}
    write_atomic(out/'results.json', result)
    status(out, 'complete', True)
    print(json.dumps({'complete': True, 'decoded_packets': result['decoded_packets'], 'qualification': fresh}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.work.resolve(), args.output.resolve())
    except BaseException as error:
        if args.output.exists():
            write_atomic(args.output/'failure.json', {'type': type(error).__name__,
                'error': str(error), 'complete': False, 'promotion_allowed': False})
        raise
