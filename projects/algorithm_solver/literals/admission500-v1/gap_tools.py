"""Write and qualify the newly written problems that complete the 500.

  gap_tools.py freeze   --work DIR                     write DIR/gap/gap-contract.json (refuses to overwrite)
  gap_tools.py packets  --work DIR                     writer packets: statement, signature, public examples
  gap_tools.py public   --work DIR --id N --file F [--extra X.json]
                                                       run F on public examples only, show actual vs expected
  gap_tools.py submit   --work DIR --id N --file F     record the single submission for N (immutable)
  gap_tools.py qualify  --work DIR                     qualify every submission not yet qualified
  gap_tools.py status   --work DIR                     selection, replacements and outcomes so far

Writers see only DIR/gap/packets/<id>/ and the public runner. Independent cases and expected
values stay host-side; qualification output reports pass or fail per problem, never cases.
"""
import argparse, ast, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stage
from stage import P, sha, write, CONSTRUCTORS, LIMITS
from inventory import test_hash_forms, source_traits

NODE_KEYS = {'__list_node__', '__tree_node__'}
GAP_CODE = [HERE / 'gap_tools.py', HERE / 'gap.py', HERE / 'stage.py', HERE / 'qualify_rules.py', HERE / 'harness.cjs',
            P / 'algsolve/judge/sandbox.py', P / 'algsolve/judge/judge.py', P / 'literals/verify_execution.py']
WRITER_RULES = """\
Write one JavaScript solution for this problem.

Interface: define the algorithm as a named function, then end the file with

    class Solution {
      %(method)s(%(params)s) {
        return %(impl)s(%(params)s);
      }
    }

forwarding the same arguments in the same order (the external method is one return
statement). Python types in the signature map to JavaScript arrays, numbers, strings and
booleans. Optional[ListNode] / Optional[TreeNode] arrive as {val, next} / {val, left, right}
objects or null; to build new nodes write `new ListNode(val, next)` / `new TreeNode(val,
left, right)` and do not define those classes (the exact constructor line is appended and
charged). Return values are compared exactly; integers beyond 2^53-1 must be returned as
BigInt.

Rules: plain ECMAScript, no require/import, no globals beyond the language. Do not modify
input arrays or objects unless the problem asks for it, and do not return an input array
or object itself. Meet the stated constraints within about 3 CPU seconds per 16 calls
under `node --jitless`. No special cases keyed to particular inputs or outputs.

You see only this statement and its public examples. You may test with the public runner
as often as you like and add your own examples from the statement. Submit once.
"""


def ordered(work):
    g = json.loads((HERE / 'evidence/gap-selection.json').read_text())
    am = json.loads((HERE / 'evidence/gap-amendment-001.json').read_text())
    assert am['amends_sha256'] == sha((HERE / 'evidence/gap-selection.json').read_bytes())
    skip = {x['id'] for x in am['skipped']}
    # Amendment 001 applies to replacements too: skip any problem whose cases expect a non-finite value.
    for d in g['quota']:
        for pid in g['selected'][d] + g['replacement_order'][d]:
            sets = g['rows'].get(str(pid), {}).get('independent_sets', [])
            if any('"__float__"' in (P / 'data/derived' / t['path']).read_text() for t in sets): skip.add(pid)
    return g, skip


def freeze(work):
    d = work / 'gap'; d.mkdir(exist_ok=True); out = d / 'gap-contract.json'
    assert not out.exists(), 'gap contract already frozen'
    g, skip = ordered(work)
    write(out, {'schema': 'gamma.literal-admission500-gap-contract.v1',
                'selection_sha256': sha((HERE / 'evidence/gap-selection.json').read_bytes()),
                'amendment_sha256': sha((HERE / 'evidence/gap-amendment-001.json').read_bytes()),
                'quota': g['quota'], 'writer_rules': WRITER_RULES,
                'pass_rule': 'Every public and independent case passes the stage oracle (qualify_rules.judge_case) in the stage harness with stage limits. For problems without node-encoded arguments, every call leaves its arguments unchanged (args_before equals args_after) and the result shares no object with the arguments. Node problems record both checks without requiring them.',
                'submission_rule': 'One submission per problem, recorded by hash before any independent case runs. A failing submission is final for that problem: it is recorded with its failure classes and the next problem in the stratum order takes its place. Independent-case content is never shown to a writer.',
                'packaging': 'A submission that constructs ListNode or TreeNode without defining it gets the exact stage constructor line appended; those bytes are charged.',
                'review': 'Each passing submission gets an independent source review against its statement for input- or output-specific branches and hidden tables. A flagged submission fails.',
                'limits': LIMITS, 'code_hashes': {str(p.relative_to(P)): sha(p.read_bytes()) for p in GAP_CODE}})
    print(sha(out.read_bytes()))


def check_code(work):
    c = json.loads((work / 'gap/gap-contract.json').read_text())
    for p, h in c['code_hashes'].items(): assert sha((P / p).read_bytes()) == h, p
    return c


def packets(work):
    check_code(work); g, skip = ordered(work)
    probs = {}
    for line in (P / 'data/derived/problems.jsonl').open():
        m = json.loads(line); probs[m['uid']] = m
    root = work / 'gap/packets'; root.mkdir(parents=True, exist_ok=True)
    for d in g['quota']:
        for pid in g['selected'][d] + g['replacement_order'][d]:
            if pid in skip: continue
            m = probs[f'lcd:{pid}']
            entry = ast.literal_eval(m['entry']) if isinstance(m['entry'], str) else m['entry']
            params = ast.literal_eval(m['params']) if isinstance(m['params'], str) else m['params']
            public = ast.literal_eval(m['public_tests']) if isinstance(m['public_tests'], str) else (m['public_tests'] or [])
            pd = root / str(pid); pd.mkdir(exist_ok=True)
            names = ', '.join(n for n, _ in params)
            impl = ''.join(w.capitalize() if i else w for i, w in enumerate(m['slug'].split('-')))
            (pd / 'problem.md').write_text(
                f"# {pid}. {m['title']} ({m['difficulty']})\n\n{m['statement']}\n\n## Signature\n\n"
                f"Method `{entry['method']}`; parameters: " + ', '.join(f'`{n}`: {t}' for n, t in params) +
                f"\n\nReference (Python starter, for types only):\n\n```\n{m['starter_code']}\n```\n\n## How to write it\n\n"
                + WRITER_RULES % {'method': entry['method'], 'params': names, 'impl': impl})
            write(pd / 'public.json', {'id': pid, 'method': entry['method'], 'params': params, 'public_tests': public})
    print(len(list(root.iterdir())), 'packets')


def run_cases(source, method, cases):
    from algsolve.judge import sandbox
    from qualify_rules import judge_case
    from verify_execution import strict_object
    harness = (HERE / 'harness.cjs').read_text(); out = []
    entry = f'(...a)=>new Solution().{method}(...a)'
    for off in range(0, len(cases), LIMITS['batch_cases']):
        batch = cases[off:off + LIMITS['batch_cases']]
        res = sandbox.run(['/usr/bin/node', '--jitless', '--single-threaded', '--max-old-space-size=64', 'harness.cjs'],
                          files={'program.js': source, 'inputs.json': json.dumps({'entry': entry, 'calls': [{'args': t['args']} for t in batch]}),
                                 'harness.cjs': harness},
                          limits=sandbox.Limits(cpu_seconds=LIMITS['sandbox_cpu_seconds'], wall_seconds=LIMITS['sandbox_wall_seconds'],
                                                memory_bytes=LIMITS['sandbox_memory_bytes'], max_output_bytes=LIMITS['max_output_bytes']))
        try:
            assert res.ok, f'sandbox failure (exit {res.exit_code}, timed out {res.timed_out}): {res.stderr.decode(errors="replace")[-300:]}'
            recs = [json.loads(l, object_pairs_hook=strict_object) for l in res.stdout.splitlines()]
            assert len(recs) == len(batch) + 1 and recs[-1] == {'done': len(batch)}, 'protocol'
            for k, rec in enumerate(recs[:-1]):
                ok, o = judge_case(batch[k], rec)
                out.append({'ok': ok, 'observed': o})
        except Exception as e:
            out.extend({'ok': False, 'observed': None, 'error': str(e)} for _ in batch)
    return out


def admitted_source(text):
    return text + ''.join(CONSTRUCTORS[c] for c in source_traits(text)['external_constructors'] if c in CONSTRUCTORS)


def public(work, pid, file, extra):
    pk = json.loads((work / 'gap/packets' / str(pid) / 'public.json').read_text())
    cases = list(pk['public_tests']) + (json.loads(Path(extra).read_text()) if extra else [])
    res = run_cases(admitted_source(Path(file).read_text()), pk['method'], cases)
    for t, r in zip(cases, res):
        o = r['observed'] or {}
        print(json.dumps({'ok': r['ok'], 'args': t['args'], 'expected': t['expected'], 'actual': o.get('result'),
                          'error': o.get('error') or r.get('error')})[:600])
    print(f"{sum(r['ok'] for r in res)}/{len(res)} public examples pass")


def submit(work, pid, file):
    d = work / 'gap/submitted'; d.mkdir(parents=True, exist_ok=True); dst = d / f'{pid}.js'
    assert (work / 'gap/packets' / str(pid)).exists(), 'no packet for this problem'
    assert not dst.exists(), f'{pid} already submitted'
    b = Path(file).read_bytes(); dst.write_bytes(b)
    with (work / 'gap/submissions.jsonl').open('a') as f:
        f.write(json.dumps({'id': pid, 'sha256': sha(b), 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}) + '\n')
    print(pid, sha(b))


def qualify(work):
    check_code(work)
    subs = {}
    for line in (work / 'gap/submissions.jsonl').open():
        r = json.loads(line); subs[r['id']] = r
    qd = work / 'gap/qualification'; qd.mkdir(exist_ok=True)
    import gzip
    from inventory import LEDGER
    E = json.loads(gzip.open(LEDGER).read())['entries']
    for pid, s in sorted(subs.items()):
        if (qd / f'{pid}.json').exists(): continue
        text = (work / 'gap/submitted' / f'{pid}.js').read_text(); assert sha(text.encode()) == s['sha256']
        src = admitted_source(text)
        pk = json.loads((work / 'gap/packets' / str(pid) / 'public.json').read_text())
        cases = []
        for t in E[f'{pid:04d}:javascript']['independent_sets']:
            part, forms = test_hash_forms((P / 'data/derived' / t['path']).read_bytes()); assert t['sha256'] in forms; cases += part
        node = any(k in json.dumps([t['args'] for t in cases]) for k in NODE_KEYS)
        res = {'public': run_cases(src, pk['method'], pk['public_tests']), 'independent': run_cases(src, pk['method'], cases)}
        classes, mutation, alias = set(), 0, 0
        for group, rs in res.items():
            for r in rs:
                o = r['observed']
                if not r['ok']:
                    classes.add(f'{group}: ' + ('error' if (o is None or o.get('error')) else 'wrong answer'))
                if o:
                    if o.get('args_before') != o.get('args_after'): mutation += 1
                    if any(e[0].startswith('result') and e[1].startswith('args') for e in o.get('alias_edges') or []): alias += 1
        if not node and mutation: classes.add('input mutated')
        if not node and alias: classes.add('result aliases input')
        out = {'id': pid, 'submission_sha256': s['sha256'], 'admitted_sha256': sha(src.encode()),
               'charged_helper_bytes': len(src.encode()) - len(text.encode()), 'node_problem': node,
               'public': f"{sum(r['ok'] for r in res['public'])}/{len(res['public'])}",
               'independent': f"{sum(r['ok'] for r in res['independent'])}/{len(res['independent'])}",
               'calls_with_mutation': mutation, 'calls_with_result_alias': alias,
               'passed_execution': not classes, 'failure_classes': sorted(classes)}
        write(qd / f'{pid}.json', out)
        write(qd / f'{pid}-baseline.json', [r['observed'] for r in res['independent']])
        print(json.dumps({k: out[k] for k in ('id', 'public', 'independent', 'passed_execution', 'failure_classes')}))


def status(work):
    g, skip = ordered(work); qd = work / 'gap/qualification'; rv = work / 'gap/reviews'
    done = {int(p.stem): json.loads(p.read_text()) for p in qd.glob('*.json') if not p.stem.endswith('baseline')} if qd.exists() else {}
    reviews = {int(p.stem): json.loads(p.read_text()) for p in rv.glob('*.json')} if rv.exists() else {}
    summary = {}
    for d, q in g['quota'].items():
        order = [i for i in g['selected'][d] + g['replacement_order'][d] if i not in skip]
        passed, failed, active = [], [], []
        for pid in order:
            if len(passed) + len(active) >= q: break
            r = done.get(pid)
            ok = r and r['passed_execution'] and reviews.get(pid, {}).get('verdict') == 'pass'
            bad = r and (not r['passed_execution'] or reviews.get(pid, {}).get('verdict') == 'fail')
            (passed if ok else failed if bad else active).append(pid)
        summary[d] = {'quota': q, 'qualified': passed, 'failed': failed, 'open': active}
    print(json.dumps({d: {k: (v if k != 'qualified' else len(v)) for k, v in s.items()} for d, s in summary.items()}, indent=1))
    return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['freeze', 'packets', 'public', 'submit', 'qualify', 'status'])
    ap.add_argument('--work', type=Path, required=True); ap.add_argument('--id', type=int); ap.add_argument('--file'); ap.add_argument('--extra')
    a = ap.parse_args(); w = a.work.resolve()
    if a.step == 'public': public(w, a.id, a.file, a.extra)
    elif a.step == 'submit': submit(w, a.id, a.file)
    else: {'freeze': freeze, 'packets': packets, 'qualify': qualify, 'status': status}[a.step](w)
