"""Shared-style rewrites for the 350 frozen-500 problems outside the first 150.

  rewrite.py packets --work DIR                    rewriter packets: admitted source and statement
  rewrite.py check   --work DIR --id N --file F    parity check of a draft (all cases, at most 8 per problem)
  rewrite.py submit  --work DIR --id N --file F    record the single rewrite for N (immutable)
  rewrite.py qualify --work DIR                    qualify every submitted rewrite

Same rules as style150-v1 (STYLE.md, unchanged oracle plus strict parity with the admitted
source's recorded observation), against the frozen population500 inputs and baselines.
"""
import argparse, concurrent.futures, importlib.util, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sys.path.insert(0, str(LIT / 'admission500-v1')); sys.path.insert(0, str(LIT / 'style150-v1'))
from stage import P, sha, write, LIMITS
import style  # parity(), exact(), CHECK_LIMIT

FROZEN_SHA = '0d6cb3ff8c7bbe86909cf2d240c1bbac93d22652bedb076c45e1b142b27f4110'


def population(work):
    pub = LIT / 'admission500-v1/evidence/population-500.json'; assert sha(pub.read_bytes()) == FROZEN_SHA
    frozen = json.loads(pub.read_text())
    man = json.loads((work / 'population500/manifest.json').read_text())
    assert sha((work / 'population500/manifest.json').read_bytes()) == frozen['manifest_sha256']
    rows = {r['id']: r for r in man['rows'] if r['cohort'] != 'first-150'}
    assert len(rows) == 350
    return rows


def parity(work, pid, source, spec):
    """style.parity reads DIR/population and DIR/population-baseline; point it at the 500 copies."""
    shim = work / 'scale500' / 'shim'
    if not shim.exists():
        shim.mkdir(parents=True)
        (shim / 'population').symlink_to(work / 'population500'); (shim / 'population-baseline').symlink_to(work / 'population500-baseline')
    return style.parity(shim, pid, source, 'solve', spec, None)


def packets(work):
    rows = population(work)
    probs = {json.loads(l)['uid']: json.loads(l) for l in (P / 'data/derived/problems.jsonl').open()}
    pk = work / 'scale500/packets'; pk.mkdir(parents=True, exist_ok=True)
    for pid, r in rows.items():
        d = pk / str(pid); d.mkdir(exist_ok=True); m = probs[f'lcd:{pid}']
        (d / 'original.js').write_bytes((work / 'population500' / f'{pid}.js').read_bytes())
        (d / 'problem.md').write_text(f"# {pid}. {m['title']} ({m['difficulty']})\n\n{m['statement']}\n\n"
                                      f"Original entry: `{r['entry']}`. The rewrite is called as `solve(...)` with the same arguments in the same order.\n")
    print(len(rows), 'packets')


def check(work, pid, file):
    rows = population(work); d = work / 'scale500' / 'checks'; d.mkdir(parents=True, exist_ok=True)
    log = d / f'{pid}.jsonl'; used = len(log.read_text().splitlines()) if log.exists() else 0
    assert used < style.CHECK_LIMIT, f'{pid}: check limit reached; submit your best draft'
    text = Path(file).read_text()
    passed, ok, n, bad = parity(work, pid, text, rows[pid])
    with log.open('a') as f: f.write(json.dumps({'sha256': sha(text.encode()), 'passed': passed, 'checks': f'{ok}/{n}'}) + '\n')
    print(json.dumps({'id': pid, 'passed': passed, 'checks': f'{ok}/{n}', 'bytes': len(text.encode()), 'checks_used': used + 1, 'mismatches': bad}, indent=1)[:3000])


def submit(work, pid, file):
    d = work / 'scale500' / 'submitted'; d.mkdir(parents=True, exist_ok=True); dst = d / f'{pid}.js'
    assert pid in population(work) and not dst.exists(), f'{pid}: not in the 350 or already submitted'
    b = Path(file).read_bytes(); dst.write_bytes(b)
    with (work / 'scale500' / 'submissions.jsonl').open('a') as f:
        f.write(json.dumps({'id': pid, 'sha256': sha(b), 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}) + '\n')
    print(pid, sha(b))


def qualify(work):
    rows = population(work); d = work / 'scale500'; q = d / 'qualification'; q.mkdir(exist_ok=True)
    subs = [json.loads(l) for l in (d / 'submissions.jsonl').open()]
    with concurrent.futures.ProcessPoolExecutor(LIMITS['workers']) as pool:
        futs = {}
        for s in subs:
            if (q / f"{s['id']}.json").exists(): continue
            text = (d / 'submitted' / f"{s['id']}.js").read_text(); assert sha(text.encode()) == s['sha256']
            futs[pool.submit(parity, work, s['id'], text, rows[s['id']])] = (s, text)
        for f in concurrent.futures.as_completed(futs):
            s, text = futs[f]; passed, ok, n, bad = f.result()
            write(q / f"{s['id']}.json", {'id': s['id'], 'sha256': s['sha256'], 'bytes': len(text.encode()), 'passed': passed,
                                         'checks': f'{ok}/{n}', 'failure': None if passed else (bad[0] if bad else 'unknown')})
            print(json.dumps({'id': s['id'], 'passed': passed, 'checks': f'{ok}/{n}'}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['packets', 'check', 'submit', 'qualify']); ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--id', type=int); ap.add_argument('--file')
    a = ap.parse_args(); w = a.work.resolve()
    {'packets': lambda: packets(w), 'check': lambda: check(w, a.id, a.file), 'submit': lambda: submit(w, a.id, a.file), 'qualify': lambda: qualify(w)}[a.step]()
