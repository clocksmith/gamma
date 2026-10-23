"""One fit-only worker; launch through supervise.py for whole-job enforcement."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
LIT = HERE.parent


def arm(cohort, work, output, deadline):
    started = time.monotonic()
    c = json.loads((HERE/'contract.json').read_text())
    assert 0 < deadline-started <= c['limits']['overall_seconds']
    def expired(signum, frame):
        raise TimeoutError('worker whole-job deadline reached')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, deadline-started)
    resource.setrlimit(resource.RLIMIT_AS, (c['limits']['address_space_bytes'],)*2)
    os.sched_setaffinity(0, set(c['limits']['arm_cores'][cohort]))
    from supervise import check_contract
    check_contract(c, work)
    import implicit
    import optimize
    d = optimize.dual
    analyze = d.analyze
    # Reuse the frozen exact codec/cost writer; importing it opens no corpus.
    spec = importlib.util.spec_from_file_location('all_length_measure', LIT/'all-length-fraction-v1/run.py')
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    texts = json.loads((work/c['cohorts'][cohort]/'fit-sources.json').read_text())
    seed = json.loads((work/c['cohorts'][cohort]/'dictionary.json').read_text())
    assert set(texts) == {str(i) for i in c['fit_ids']}
    assert all(texts.values()) and set(''.join(texts.values())) <= set(d.ALPHABET)
    proof = json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text())
    receipt = next(a for a in proof['arms'] if a['arm'] == ('control' if cohort == 'R' else 'scope_joint') and a['width'] == 8)
    for pid, text in texts.items():
        assert analyze.sha(text.encode()) == receipt['per_problem'][pid]['source_sha256']
        assert receipt['qualification'][pid]['passed']
    banned = d.sel.forbidden_strings(texts)
    pool_started = time.monotonic()
    index = implicit.Index(texts, banned)
    pool_seconds = time.monotonic()-pool_started
    folder = output/f'{cohort}-flex256'
    folder.mkdir()
    def trace(row):
        row['validation_loaded'] = False
        with (folder/'trace.jsonl').open('a') as handle:
            handle.write(json.dumps(row, sort_keys=True)+'\n')
        if row['iteration'] % 100 == 0:
            print(json.dumps({'arm': cohort, **row}), flush=True)
    info, q, seed, best, generated = optimize.optimize(index, seed, c['pool']['capacity'], c['search'], trace)
    analyze.write(folder/'certificate-q.json', q)
    info['certificate']['q_sha256'] = analyze.sha((folder/'certificate-q.json').read_bytes())
    witnesses = {}
    for name, vocab in (('seed', seed), ('best', best), ('generated', generated)):
        if vocab is None:
            continue
        assert len(vocab) <= c['pool']['capacity'] and len(set(vocab)) == len(vocab)
        assert not set(vocab) & banned
        for word in vocab:
            lo, hi = implicit.occurrence_interval(texts, index.positions, word)
            assert lo < hi
        witnesses[name] = previous.measure(texts, vocab, folder/name, c['decoder_dependency_bytes'])
        assert info['certificate']['integer_lower_bound'] <= witnesses[name]['objective']
        # Metadata only: exact bans are necessary, not sufficient for M1 legality.
        supports = [implicit.occurrence_interval(texts, index.positions, word) for word in vocab]
        owners = [len({index.positions[i][0] for i in range(lo, hi)}) for lo, hi in supports]
        witnesses[name]['one_owner_entries'] = sum(count == 1 for count in owners)
        witnesses[name]['maximum_entry_length'] = max(map(len, vocab), default=0)
        witnesses[name]['semantic_reuse_audit'] = 'not_performed_relaxation_witness_only'
    assert witnesses['best']['objective'] == info['best_objective']
    result = {'cohort': cohort, 'mode': 'flex256', 'fit_problems': len(texts),
              'validation_loaded': False, 'complete': True,
              'pool_scope': c['pool']['scope'], 'pool_entries': index.distinct_allowed_entries,
              'implicit_groups': len(index.groups), 'source_characters': len(index.positions),
              'exact_ban_occurrences': sum(len(ends) for rows in index.banned_ends.values() for ends in rows),
              'maximum_entry_length_upper_bound': max(map(len, texts.values())),
              'pool_seconds': pool_seconds, 'capacity': c['pool']['capacity'],
              'mandatory_entries': 0, 'optimization': info, 'witnesses': witnesses,
              'fit_source_sha256': c['private_files'][c['cohorts'][cohort]+'/fit-sources.json'],
              'contract_sha256': analyze.sha((HERE/'contract.json').read_bytes()),
              'source_qualification': 'exact item 13 hash receipt reuse; no source execution',
              'seconds': time.monotonic()-started}
    analyze.write(folder/'results.json', result)
    print(json.dumps({'complete': cohort, 'bound': info['certificate']['integer_lower_bound'],
                      'upper': info['best_objective'], 'seconds': result['seconds']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cohort', required=True, choices=('R', 'naming'))
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--deadline', required=True, type=float)
    args = parser.parse_args()
    arm(args.cohort, args.work, args.output, args.deadline)
