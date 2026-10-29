"""Observer-alone cost of the v1 and v2 T/S JavaScript observers.

Runs each observer inside the judge sandbox with the T/S protocols' JavaScript
argv and unchanged limits (3 CPU s, 8 wall s, 1 GiB, 16 MiB output). The
programs are trivial synthetic no-ops written here and the packets are
synthetic trees/lists generated here. No numbered candidate, problem
statement or reference case is read. Each program prints its process CPU
time to stderr on exit. A SIGKILLed run prints nothing, and is reported by
exit status and wall time.

--phases additionally runs a diagnostic entry (phase_probe.cjs, published in
the sandbox as harness.cjs) that wraps build/snapshot/JSON to attribute CPU.

Usage (on the Linux executor):
  python3 measure_observer_cost.py --algorithm-solver <repo>/projects/algorithm_solver \
      --reps 5 [--phases] --output observer-cost-measurements.json
The v1 and v2 observer directories are resolved as siblings of this file.
"""
import argparse
import hashlib
import json
import statistics
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOGUE = HERE.parent
ARGV = ['/usr/bin/node', '--jitless', '--single-threaded', '--max-old-space-size=256', 'harness.cjs']
CPU = "process.on('exit',()=>{const u=process.cpuUsage();process.stderr.write('CPU '+JSON.stringify({cpu_ms:(u.user+u.system)/1000})+'\\n');});\n"
PROGRAMS = {
    'tree_required': "function TreeNode(val){this.val=val;this.left=null;this.right=null;}\nfunction lowestCommonAncestor(root,p,q){return p;}\nmodule.exports={TreeNode,lowestCommonAncestor};\n",
    'list': "function ListNode(val,next){this.val=(val===undefined?0:val);this.next=(next===undefined?null:next);}\nfunction isPalindrome(head){return true;}\nmodule.exports={ListNode,isPalindrome};\n",
    'tree_default': "function TreeNode(val,left,right){this.val=(val===undefined?0:val);this.left=(left===undefined?null:left);this.right=(right===undefined?null:right);}\nfunction countNodes(root){return 0;}\nmodule.exports={TreeNode,countNodes};\n",
}


def chain(n):
    return {'values': list(range(n)), 'left': [None] * n, 'right': [i + 1 if i + 1 < n else None for i in range(n)], 'root': 0}


def complete(n):
    return {'values': list(range(n)), 'left': [2 * i + 1 if 2 * i + 1 < n else None for i in range(n)],
            'right': [2 * i + 2 if 2 * i + 2 < n else None for i in range(n)], 'root': 0 if n else None}


def balanced_bst(n):
    left, right, stack, root = [None] * n, [None] * n, [(0, n - 1, None, None)], None
    while stack:
        lo, hi, parent, side = stack.pop()
        if lo > hi:
            continue
        mid = (lo + hi) // 2
        if parent is None:
            root = mid
        elif side == 'l':
            left[parent] = mid
        else:
            right[parent] = mid
        stack.append((lo, mid - 1, mid, 'l'))
        stack.append((mid + 1, hi, mid, 'r'))
    return {'values': list(range(n)), 'left': left, 'right': right, 'root': root}


def flat_list(n):
    return {'values': [1] * n, 'next': [i + 1 if i + 1 < n else None for i in range(n)], 'head': 0}


N = 100000
# Batch shapes mirror the failed plans: small-large-small (235/236),
# large-repeat (234 at 100k, 222 at 50k), plus single-call references.
SCENARIOS = {
    'T235 chain [3,100k,3]': ('t', 235, 'tree_required', [[chain(3), 0, 2], [chain(N), N // 2, N - 1], [chain(3), 0, 2]]),
    'T235 balanced [3,100k,3]': ('t', 235, 'tree_required', [[balanced_bst(3), 0, 2], [balanced_bst(N), 0, N - 1], [balanced_bst(3), 0, 2]]),
    'T236 complete [3,100k,3]': ('t', 236, 'tree_required', [[complete(3), 1, 2], [complete(N), N // 2, N - 1], [complete(3), 1, 2]]),
    'T234 list [100k,100k]': ('t', 234, 'list', [[flat_list(N)], [flat_list(N)]]),
    'S222 complete [50k,50k]': ('s', 222, 'tree_default', [[complete(50000)], [complete(50000)]]),
    'T235 chain [100k]': ('t', 235, 'tree_required', [[chain(N), N // 2, N - 1]]),
    'T234 list [100k]': ('t', 234, 'list', [[flat_list(N)]]),
    'S222 complete [50k]': ('s', 222, 'tree_default', [[complete(50000)]]),
    'T235 chain [50k]': ('t', 235, 'tree_required', [[chain(50000), 25000, 49999]]),
    'T234 list [50k]': ('t', 234, 'list', [[flat_list(50000)]]),
}


def observer_dir(lane, version):
    return CATALOGUE / f'continuation-{lane}-observers-20261028-{version}'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--algorithm-solver', type=Path, required=True, help='projects/algorithm_solver of a checkout holding algsolve/judge/sandbox.py')
    parser.add_argument('--reps', type=int, default=5)
    parser.add_argument('--phases', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.algorithm_solver))
    from algsolve.judge import sandbox
    limits = sandbox.Limits(cpu_seconds=3, wall_seconds=8, memory_bytes=1024**3, max_output_bytes=16 * 1024**2)
    sandbox_sha = hashlib.sha256((args.algorithm_solver / 'algsolve/judge/sandbox.py').read_bytes()).hexdigest()
    probe = (HERE / 'phase_probe.cjs').read_bytes()
    results, observers = [], {}
    for name, (lane, pid, program, calls) in SCENARIOS.items():
        packet = json.dumps({'schema': f'gamma.{lane}-official-packet.v1', 'problem_id': pid, 'calls': [{'args': a} for a in calls]}, separators=(',', ':')).encode()
        for version in ('v1', 'v2'):
            base = observer_dir(lane, version)
            helpers = {f: (base / f).read_bytes() for f in ('harness.cjs', 'native_graphs.cjs')}
            observers[f'{lane}-{version}'] = {f: hashlib.sha256(b).hexdigest() for f, b in helpers.items()}
            runs, digests = [], set()
            for _ in range(args.reps):
                files = {'program.cjs': CPU + PROGRAMS[program], 'inputs.json': packet, **helpers}
                res = sandbox.run(ARGV, files=files, limits=limits)
                cpu = [json.loads(line[4:])['cpu_ms'] for line in res.stderr.decode(errors='replace').splitlines() if line.startswith('CPU ')]
                lines = res.stdout.decode(errors='replace').splitlines()
                digests.add(hashlib.sha256(res.stdout).hexdigest())
                runs.append({'exit_code': res.exit_code, 'signal': res.signal, 'timed_out': res.timed_out, 'wall_seconds': round(res.wall_seconds, 3),
                             'process_cpu_ms': cpu[0] if cpu else None, 'stdout_bytes': len(res.stdout),
                             'complete_records': sum(1 for line in lines if line.startswith('{"i"')),
                             'error_records': sum(1 for line in lines if line.startswith('{"i"') and '"error"' in line[:40])})
            cpus = [r['process_cpu_ms'] for r in runs if r['process_cpu_ms'] is not None]
            row = {'scenario': name, 'observer': version, 'problem_id': pid, 'calls': len(calls), 'input_bytes': len(packet), 'runs': runs,
                   'all_exit_zero': all(r['exit_code'] == 0 for r in runs), 'median_process_cpu_ms': statistics.median(cpus) if cpus else None,
                   'stdout_sha256': sorted(digests)}
            if args.phases:
                files = {'program.cjs': PROGRAMS[program], 'inputs.json': packet, 'harness.cjs': probe, 'observer.cjs': helpers['harness.cjs'], 'native_graphs.cjs': helpers['native_graphs.cjs']}
                res = sandbox.run(ARGV, files=files, limits=limits)
                phase = [json.loads(line[7:]) for line in res.stderr.decode(errors='replace').splitlines() if line.startswith('PHASES ')]
                row['phase_probe'] = {'exit_code': res.exit_code, 'signal': res.signal, 'wall_seconds': round(res.wall_seconds, 3), 'phases_ms': phase[0] if phase else None}
            results.append(row)
            print(f"{name:26s} {version} exit={[r['exit_code'] for r in runs]} cpu_ms={row['median_process_cpu_ms']} wall={[r['wall_seconds'] for r in runs]}"
                  + (f" phases={row['phase_probe']['phases_ms']}" if args.phases else ''), flush=True)
    for name in {r['scenario'] for r in results}:
        pair = {r['observer']: r for r in results if r['scenario'] == name}
        if pair['v1']['all_exit_zero'] and pair['v2']['all_exit_zero']:
            pair['v2']['stdout_identical_to_v1'] = pair['v1']['stdout_sha256'] == pair['v2']['stdout_sha256']
    import platform
    import subprocess
    node = subprocess.run(['/usr/bin/node', '--version'], capture_output=True, text=True).stdout.strip()
    report = {'schema': 'gamma.ts-observer-cost-measurement.v1', 'executor': 'Linux judge executor (hostname omitted)', 'kernel': platform.release(),
              'node': node, 'argv': ARGV, 'limits': asdict(limits), 'sandbox_sha256': sandbox_sha, 'reps': args.reps, 'observers': observers,
              'programs': 'synthetic no-op TreeNode/ListNode programs defined in this script', 'candidate_executions': 0,
              'problem_statements_or_reference_cases_read': False, 'results': results,
              'interpretation': 'Observer-alone cost under the unchanged sandbox. Not candidate qualification.'}
    args.output.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
