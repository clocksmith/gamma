#!/usr/bin/env python3
"""Exact witness-rule coverage at chosen budgets, using the frozen six-bit model unchanged.

Loads model.py as extracted from the pinned commit, builds the witness-rule graph for compact matched80
and solves 'B1' (most programs covered with at most BUDGET entries). One JSON line per budget.

    witness_milp.py GAMMA_CHECKOUT FROZEN_DIR OUT.jsonl WORKERS SECONDS BUDGET,BUDGET,...
"""
import hashlib, importlib.util, json, subprocess, sys, time
from multiprocessing import Pool
REPO, FROZEN, OUT, WORKERS, SECONDS = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), float(sys.argv[5])
BUDGETS = [int(x) for x in sys.argv[6].split(',')]
PIN, ROOT = '59ff04415ff2afd04ff2ed451340f4f02852bf18', 'projects/algorithm_solver/literals/'
MODEL_SHA = 'df0ee24136a4a0ac40198822327c7c04cf570b8b24dfde5b29ee74712c35ab48'


def blob(path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{PIN}:{ROOT}{path}'])


def texts():
    ids = set(json.loads(blob('matched80-v1/labels/ids.json')))
    rows = [r for r in json.loads(blob('scale-v2/generated/manifest.json'))['rows'] if r['variant'] == 'compact' and r['id'] in ids]
    assert len(rows) == 80
    return {str(r['id']): blob('scale-v2/generated/' + r['file']).decode('utf-8') for r in rows}


def work(budget):
    assert hashlib.sha256(open(FROZEN + '/model.py', 'rb').read()).hexdigest() == MODEL_SHA
    spec = importlib.util.spec_from_file_location('frozen_model', FROZEN + '/model.py')
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    graph = model.Graph(texts(), 'W')
    began = time.monotonic()
    res = model.solve_milp(graph, 'B1', SECONDS, budget=budget)
    rec = {'budget': budget, 'seconds': round(time.monotonic() - began, 1), 'status': int(res.status), 'message': str(res.message)[:120],
           'mip_dual_bound': None if getattr(res, 'mip_dual_bound', None) is None else float(res.mip_dual_bound),
           'mip_gap': None if getattr(res, 'mip_gap', None) is None else float(res.mip_gap), 'model_size': graph.size()}
    if res.x is not None:
        shared, parses = model.solution(graph, res)
        used = sorted({s for r in parses.values() if r for s, _ in r[2]})
        rec.update(objective=float(res.fun), covered=sum(r is not None for r in parses.values()), entries=len(used), vocabulary=used)
    return rec


if __name__ == '__main__':
    with Pool(WORKERS) as pool, open(OUT, 'a') as out:
        for rec in pool.imap_unordered(work, BUDGETS):
            out.write(json.dumps(rec) + '\n')
            out.flush()
            print(rec['budget'], rec.get('covered'), rec['mip_dual_bound'], rec['seconds'], rec['message'], flush=True)
