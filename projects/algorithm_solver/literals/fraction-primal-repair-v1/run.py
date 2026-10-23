"""Bounded fit-only worker. Contract intentionally unavailable before freeze."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import time

HERE = Path(__file__).resolve().parent


def arm(cohort, work, output, outer_deadline):
    started = time.monotonic(); c = json.loads((HERE / 'contract.json').read_text())
    deadline = min(outer_deadline, started + c['limits']['cohort_seconds'])
    folder = output / cohort; folder.mkdir(); phase = 'preflight'
    def expired(*_):
        raise TimeoutError('worker entire-phase deadline reached')
    signal.signal(signal.SIGALRM, expired); signal.setitimer(signal.ITIMER_REAL, max(.001, deadline - started))
    resource.setrlimit(resource.RLIMIT_AS, (c['limits']['address_space_bytes'],) * 2)
    os.sched_setaffinity(0, set(c['limits']['arm_cores'][cohort]))
    from backend import CERT_KEYS, inputs, measure, sha, write, dual
    try:
        from supervise import check_contract
        check_contract(c, work)
        import model
        import pool
        def status(value):
            write(folder / 'status.json', {'phase': value, 'complete': False})
        status(phase)
        phase = 'source_identity'; status(phase)
        texts, seed, q, parent = inputs(c, work, cohort)
        phase = 'index_and_pool'; status(phase)
        bans = dual.sel.forbidden_strings(texts); index = pool.implicit.Index(texts, bans)
        cert = index.certificate(q, c['pool']['capacity'], c['pool']['denominator'])
        for key in CERT_KEYS:
            assert cert[key] == parent['certificate'][key]
        candidates, info = pool.build(index, q, seed, c['pool']['denominator'], c['pool']['capacity'], c['pool']['entries'])
        write(folder / 'pool.json', candidates); write(folder / 'pool-provenance.json', info)
        phase = 'model'; status(phase)
        m = model.build(texts, candidates, c['pool']['capacity'], seed, bans, **c['construction'])
        model_hash = model.fingerprint(m); witnesses = {'seed': measure(texts, seed, folder / 'seed', c['decoder_dependency_bytes'])}
        assert witnesses['seed']['objective'] == m['initial'] == parent['witnesses']['seed']['objective']
        results = {}
        for name in c['solve_order'][cohort]:
            phase = name; status(phase)
            assert model.fingerprint(m) == model_hash
            vocab, receipt, replay = model.solve(m, texts, candidates, name == 'warm', c['search']['seconds'], bans, c['search']['random_seed'])
            assert receipt['model_sha256'] == model_hash
            if receipt['feasible']:
                witnesses[name] = measure(texts, vocab, folder / name, c['decoder_dependency_bytes'])
                assert witnesses[name]['objective'] == replay['F']
                assert witnesses[name]['characters'] == replay['C'] and witnesses[name]['selections']['total'] == replay['N']
            results[name] = receipt
            write(folder / f'{name}-solver.json', receipt)
        result = {'cohort': cohort, 'complete': True, 'validation_loaded': False,
                  'fit_problems': len(texts), 'fit_source_sha256': parent['fit_source_sha256'],
                  'parent_q_sha256': parent['certificate']['q_sha256'],
                  'parent_full_class_certificate': {k: cert[k] for k in CERT_KEYS},
                  'pool_sha256': sha(folder / 'pool.json'), 'pool_provenance_sha256': sha(folder / 'pool-provenance.json'),
                  'pool_counts': {k: v for k, v in info.items() if k != 'provenance'},
                  'model_sha256': model_hash, 'arcs': m['arcs'], 'variables': m['variables'], 'transitions': m['transitions'],
                  'build_seconds': m['build_seconds'], 'solve_order': c['solve_order'][cohort], 'solvers': results,
                  'witnesses': witnesses, 'contract_sha256': sha(HERE / 'contract.json'), 'seconds': time.monotonic() - started}
        assert result['seconds'] <= c['limits']['cohort_seconds']
        write(folder / 'results.json', result); write(folder / 'status.json', {'phase': 'complete', 'complete': True})
    except BaseException as error:
        write(folder / 'failure.json', {'phase': phase, 'complete': False, 'exception': type(error).__name__,
              'partial_witnesses_promoted': False, 'validation_loaded': False, 'seconds': time.monotonic() - started})
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--cohort', choices=('R', 'naming'), required=True)
    p.add_argument('--work', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--deadline', type=float, required=True); a = p.parse_args()
    arm(a.cohort, a.work, a.output, a.deadline)
