"""Classify why failed gap submissions failed (reporting only; never shown to writers).

  gap_diagnose.py --work DIR   writes DIR/gap/diagnosis.json: per failed problem, counts of
                               time-limit, memory-limit, stack-overflow, other-error and wrong-answer cases
"""
import argparse, glob, gzip, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from stage import P, LIMITS, write
from gap_tools import admitted_source
from inventory import LEDGER, test_hash_forms


def classify(work):
    from algsolve.judge import sandbox
    from qualify_rules import judge_case
    from verify_execution import strict_object
    E = json.loads(gzip.open(LEDGER).read())['entries']
    harness = (HERE / 'harness.cjs').read_text(); out = {}
    for f in sorted(glob.glob(str(work / 'gap/qualification/*.json'))):
        if f.endswith('-baseline.json'): continue
        q = json.loads(Path(f).read_text())
        if q['passed_execution']: continue
        pid = q['id']; src = admitted_source((work / 'gap/submitted' / f'{pid}.js').read_text())
        method = json.loads((work / 'gap/packets' / str(pid) / 'public.json').read_text())['method']
        cases = []
        for t in E[f'{pid:04d}:javascript']['independent_sets']:
            part, _ = test_hash_forms((P / 'data/derived' / t['path']).read_bytes()); cases += part
        counts = {'time limit': 0, 'memory limit': 0, 'stack overflow': 0, 'other error': 0, 'wrong answer': 0, 'passed': 0}
        for off in range(0, len(cases), LIMITS['batch_cases']):
            batch = cases[off:off + LIMITS['batch_cases']]
            res = sandbox.run(['/usr/bin/node', '--jitless', '--single-threaded', '--max-old-space-size=64', 'harness.cjs'],
                              files={'program.js': src, 'harness.cjs': harness,
                                     'inputs.json': json.dumps({'entry': f'(...a)=>new Solution().{method}(...a)', 'calls': [{'args': t['args']} for t in batch]})},
                              limits=sandbox.Limits(cpu_seconds=LIMITS['sandbox_cpu_seconds'], wall_seconds=LIMITS['sandbox_wall_seconds'],
                                                    memory_bytes=LIMITS['sandbox_memory_bytes'], max_output_bytes=LIMITS['max_output_bytes']))
            err = res.stderr.decode(errors='replace')
            recs = []
            for line in res.stdout.splitlines():
                try: recs.append(json.loads(line, object_pairs_hook=strict_object))
                except Exception: pass
            done = {r['i']: r for r in recs if isinstance(r.get('i'), int)}
            for k, t in enumerate(batch):
                r = done.get(k)
                if r is None:
                    kind = 'memory limit' if 'heap out of memory' in err or 'Allocation failed' in err else \
                           'time limit' if res.timed_out or res.exit_code in (137, 152, -9, -24) else 'other error'
                    counts[kind] += 1
                elif r.get('error'):
                    counts['stack overflow' if 'call stack' in r['error'] else 'other error'] += 1
                else:
                    counts['passed' if judge_case(t, r)[0] else 'wrong answer'] += 1
        primary = max((k for k in counts if k != 'passed'), key=lambda k: counts[k])
        out[pid] = {'cases': len(cases), 'counts': counts, 'primary': primary}
        print(pid, primary, counts, flush=True)
    write(work / 'gap/diagnosis.json', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True)
    classify(ap.parse_args().work.resolve())
