"""Author-local run of this cohort's own candidates on every generated case; not qualification.

For each problem id, builds cases with cases.build_cases(pid, include_maximum=True) and calls:
  * python3: python/<pid>.py `solve(*args)`, plus the official `Solution().<name>` wrapper, or for a class
    problem the native class driven directly through the operation trace
  * node --jitless: javascript/<pid>.js callable export `solve(...args)`, plus the official named export
    (native class driven through the trace for a class problem)
Each call gets a fresh deep copy of the arguments; the copy must be unchanged afterwards. Results are compared
with the expected value from the cohort reference under JSON typing (Python: bool, int, float, str, None, list
and dict kinds must match; JavaScript: JSON numbers compare by value). Per-call CPU time is measured with
time.process_time (Python) and process.cpuUsage user+system (JavaScript). Writes JSON to stdout.

Run: python3 run_candidates.py > /dev/null   (exit status 1 on any failure)
"""
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLOW_SECONDS = 1.0


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = load('cohort_cases_' + HERE.name.replace('-', '_'), HERE / 'cases.py')
CONTRACTS = {p['id']: p for p in json.loads((HERE / 'contracts.json').read_text())['problems']}


def kind(v):
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'bool'
    if isinstance(v, int):
        return 'int'
    if isinstance(v, float):
        return 'float'
    if isinstance(v, str):
        return 'str'
    if isinstance(v, (list, tuple)):
        return 'list'
    if isinstance(v, dict):
        return 'dict'
    return 'other:' + type(v).__name__


def exact(got, want, json_numbers=False):
    kg, kw = kind(got), kind(want)
    if json_numbers and kg in ('int', 'float') and kw in ('int', 'float'):
        return got == want
    if kg != kw:
        return False
    if kg == 'list':
        return len(got) == len(want) and all(exact(a, b, json_numbers) for a, b in zip(got, want))
    if kg == 'dict':
        return set(got) == set(want) and all(exact(got[k], want[k], json_numbers) for k in got)
    return got == want


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


JS_RUNNER = r"""
const fs = require('fs');
const job = JSON.parse(fs.readFileSync(0, 'utf8'));
const mod = require(job.path);
const solve = typeof mod === 'function' ? mod : mod.solve;
function mark(v) {
  if (v === undefined) return {__undefined__: true};
  if (typeof v === 'number' && !Number.isFinite(v)) return {__nonfinite__: String(v)};
  if (typeof v === 'bigint') return {__bigint__: String(v)};
  if (Array.isArray(v)) return v.map(mark);
  if (v !== null && typeof v === 'object') {
    const o = {};
    for (const k of Object.keys(v)) o[k] = mark(v[k]);
    return o;
  }
  return v;
}
function native(Cls) {
  return (ops, argLists) => {
    const receiver = new Cls(...argLists[0]);
    const out = [null];
    for (let i = 1; i < ops.length; i++) {
      const r = receiver[ops[i]](...argLists[i]);
      out.push(r === undefined ? null : r);
    }
    return out;
  };
}
function call(fn, args) {
  const copy = JSON.parse(JSON.stringify(args));
  const before = JSON.stringify(copy);
  const t0 = process.cpuUsage();
  let value, error = null;
  try { value = fn(...copy); } catch (e) { error = String(e && e.stack || e); }
  const d = process.cpuUsage(t0);
  return {value: mark(value), error, unchanged: JSON.stringify(copy) === before, cpu: (d.user + d.system) / 1e6};
}
const out = [];
for (const args of job.cases) {
  const primary = call(solve, args);
  let official = null;
  if (job.official && job.native) official = call(native(mod[job.official]), args);
  else if (job.official && typeof mod[job.official] === 'function') official = call(mod[job.official], args);
  else if (job.official) official = {missing: true};
  out.push({primary, official});
}
process.stdout.write(JSON.stringify(out));
"""


def native(cls, ops, arg_lists):
    receiver = cls(*arg_lists[0])
    return [None] + [getattr(receiver, op)(*a) for op, a in zip(ops[1:], arg_lists[1:])]


def run_python(pid, rows, official):
    module = load(f'cohort_candidate_{HERE.name.replace("-", "_")}_{pid}', HERE / 'python' / f'{pid}.py')
    results = []
    for row in rows:
        entry = {}
        targets = [('solve', module.solve)]
        if official and isinstance(getattr(module, official, None), type):
            targets.append(('official', lambda ops, arg_lists, _c=getattr(module, official): native(_c, ops, arg_lists)))
        elif official and hasattr(module, 'Solution') and hasattr(module.Solution, official):
            targets.append(('official', lambda *a, _m=official: getattr(module.Solution(), _m)(*a)))
        elif official:
            entry['official'] = {'missing': True}
        for label, fn in targets:
            args = copy.deepcopy(row['args'])
            error = None
            t0 = time.process_time()
            try:
                value = fn(*args)
            except Exception as exc:  # recorded as failure
                value, error = None, repr(exc)
            cpu = time.process_time() - t0
            entry[label] = {'ok': error is None and exact(value, row['expected']), 'unchanged': args == row['args'],
                            'cpu': cpu, 'error': error, 'value': value}
        results.append(entry)
    return results


def ops_first(rows):
    args = rows[0]['args'] if rows else []
    if args and isinstance(args[0], list) and args[0] and isinstance(args[0][0], str) and len(args) == 2:
        return args[0][0]
    return None


def run_javascript(pid, rows, official):
    job = {'path': str(HERE / 'javascript' / f'{pid}.js'), 'cases': [r['args'] for r in rows], 'official': official,
           'native': official is not None and official == (ops_first(rows) or '')}
    proc = subprocess.run(['node', '--jitless', '-e', JS_RUNNER], input=json.dumps(job), capture_output=True, text=True)
    if proc.returncode != 0:
        return [{'solve': {'ok': False, 'unchanged': False, 'cpu': 0.0, 'error': proc.stderr[-400:], 'value': None}}
                for _ in rows]
    results = []
    for row, got in zip(rows, json.loads(proc.stdout)):
        entry = {}
        for label, key in (('solve', 'primary'), ('official', 'official')):
            g = got[key]
            if g is None:
                continue
            if g.get('missing'):
                entry[label] = {'missing': True}
                continue
            entry[label] = {'ok': g['error'] is None and exact(g['value'], row['expected'], json_numbers=True),
                            'unchanged': g['unchanged'], 'cpu': g['cpu'], 'error': g['error'], 'value': g['value']}
        results.append(entry)
    return results


def main():
    report = {'problems': {}}
    failed = False
    for pid in CASES.PROBLEM_IDS:
        rows = CASES.build_cases(pid, include_maximum=True)
        official = CONTRACTS[pid]['official_interface'].get('name')
        problem = {'cases': len(rows)}
        for language, runner, src in (('python', run_python, HERE / 'python' / f'{pid}.py'),
                                      ('javascript', run_javascript, HERE / 'javascript' / f'{pid}.js')):
            res = runner(pid, rows, official)
            solve_pass = sum(1 for r in res if r['solve']['ok'] and r['solve']['unchanged'])
            off = [r['official'] for r in res if 'official' in r]
            failures = []
            for i, (row, r) in enumerate(zip(rows, res)):
                for label in ('solve', 'official'):
                    x = r.get(label)
                    if x and not x.get('missing') and not (x['ok'] and x['unchanged']):
                        failures.append({'case_index': i, 'entry': label, 'args': str(row['args'])[:160],
                                         'expected': str(row['expected'])[:160], 'got': str(x['value'])[:160],
                                         'unchanged': x['unchanged'], 'error': x['error']})
            cpus = [x['cpu'] for r in res for x in r.values() if 'cpu' in x]
            problem[language] = {
                'source_sha256': sha(src),
                'solve_passed': solve_pass,
                'official_entry': (None if not off else 'missing' if any(o.get('missing') for o in off)
                                   else sum(1 for o in off if o['ok'] and o['unchanged'])),
                'heaviest_call_cpu_seconds': round(max(cpus), 4) if cpus else None,
                'over_1s': sum(1 for c in cpus if c > SLOW_SECONDS),
                'failures': failures,
            }
            failed = failed or bool(failures) or solve_pass != len(rows)
        report['problems'][str(pid)] = problem
    json.dump(report, sys.stdout, indent=1, default=str)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
