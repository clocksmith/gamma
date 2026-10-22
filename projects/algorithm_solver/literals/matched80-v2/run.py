"""Iteration 2 on the 80 compact sources: span ranking versus a designed hybrid, at three shortlist widths.

Reuses the frozen matched80-v1 search (scale-v2 learn with an injected candidate source),
inputs, designed pool and verification. Only the candidate source and shortlist width vary.
Nothing executes candidate source.
"""
import argparse
import importlib.util
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('matched80_v1', ROOT.parent / 'matched80-v1/run.py')
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
base, joint, sha, write = v1.base, v1.joint, v1.sha, v1.write
RANKINGS = ('span', 'hybrid')
WIDTHS = (12, 48, 192)


def candidates(ranking, designed, width):
    """span: scale-v2 proposals in scale-v2 order. hybrid: 3/4 of the shortlist from that
    order, 1/4 from designed pieces ranked by the shared matched80-v1 estimator."""
    designed_slots = width // 4 if ranking == 'hybrid' else 0
    def propose(texts, vocab, current, retired):
        mined = [s for s in base.proposals(texts, vocab, current) if s not in retired]
        if not designed_slots:
            return mined
        present = set(vocab) | retired
        head = mined[:width - designed_slots]
        pieces = [s for s in designed if s not in present and s not in head and sum(s in t for t in texts.values()) >= 2]
        ranked = v1.rank(pieces, '\x00'.join(texts.values()), vocab)[:designed_slots]
        # Designed slots hold pieces not already in the mined head; unused slots fall back to mined order.
        return head + ranked + [s for s in mined[len(head):] if s not in ranked]
    return propose


def run_fixed(contract, out, ranking, width):
    texts, _ = v1.load_inputs(v1_contract())
    designed = v1.designed_pool(v1_contract())['compact']
    limits = {'search_seconds_per_arm': contract['fixed_bounds']['search_seconds_per_arm'], 'shortlist': width,
              'max_trials_per_arm': contract['fixed_bounds']['max_trials_by_shortlist'][str(width)]}
    snapshots, trace = v1.learn(texts['compact'], limits, candidates(ranking, designed, width))
    write(out / f'fixed-{ranking}-{width}-trace.json', trace)
    rows = []
    for size, (vocab, seqs) in snapshots.items():
        folder = out / f'fixed-{ranking}-{width}-{size}'
        base.save(folder, texts['compact'], vocab, seqs, size.bit_length() - 1, 'compact', f'{ranking}-shortlist-{width}')
        rows.append(v1.verify_and_extend(folder, texts['compact'], vocab, v1.provenance_of(designed),
                                         {'ranking': ranking, 'shortlist': width, 'size': size, 'kind': 'fixed'}))
    write(out / f'fixed-{ranking}-{width}-resources.json', {'search_seconds': trace['elapsed_seconds'], 'trials': trace['exact_candidate_trials'],
                                                           'time_limit_reached': trace['time_limit_reached'], 'trial_limit_reached': trace['trial_limit_reached'], **v1.peak_memory()})
    return rows


def run_polish(contract, out, size):
    """joint-v1 improve() with mined proposals from the best fixed arm of this size, compact and canonical both eligible."""
    texts, metadata = v1.load_inputs(v1_contract())
    sources = {int(pid): {style: texts[style][pid] for style in v1.STYLES} for pid in texts['canonical']}
    width = size.bit_length() - 1
    arms = [(json.loads((out / f'fixed-{r}-{w}-{size}/manifest.json').read_text())['metrics'], f'fixed-{r}-{w}-{size}') for r in RANKINGS for w in WIDTHS]
    best_metrics, best_name = min(arms, key=lambda a: (a[0]['selections'], a[0]['package_bytes'], a[1]))
    vocab = json.loads((out / best_name / 'dictionary.json').read_text())
    start, _ = joint.prune(sources, joint.evaluate(sources, vocab, width), width)
    final, trace = v1.improve(sources, start, width, 'input', contract['polish_bounds'], v1.joint_candidates('mined', []))
    assert (final['selections'], final['package_bytes']) <= (best_metrics['selections'], best_metrics['package_bytes'])
    write(out / f'polish-{size}-trace.json', {'start_arm': best_name, 'initial': joint.brief(start), **trace})
    folder = out / f'polish-{size}'
    joint.save(folder, sources, metadata, final, width, 'joint-polish')
    chosen = {str(pid): sources[pid][v] for pid, v in final['chosen'].items()}
    designed = v1.designed_pool(v1_contract())['compact']
    met = v1.verify_and_extend(folder, chosen, final['vocab'], v1.provenance_of(designed),
                               {'kind': 'polish', 'size': size, 'start_arm': best_name, 'start_selections': best_metrics['selections']})
    write(out / f'polish-{size}-resources.json', {'search_seconds': trace['elapsed_seconds'], 'trials': trace['trials'], 'stop': trace['stop'], **v1.peak_memory()})
    return met


def v1_contract():
    return json.loads((ROOT.parent / 'matched80-v1/contract.json').read_text())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--fixed', nargs=2, metavar=('RANKING', 'WIDTH'))
    p.add_argument('--polish', metavar='SIZE')
    a = p.parse_args()
    contract = json.loads((ROOT / 'contract.json').read_text())
    for rel, digest in contract['inputs'].items():
        if sha((ROOT / rel).read_bytes()) != digest:
            raise ValueError(f'frozen input changed: {rel}')
    if a.fixed:
        print(json.dumps(run_fixed(contract, a.output, a.fixed[0], int(a.fixed[1]))), flush=True)
        return
    if a.polish:
        print(json.dumps(run_polish(contract, a.output, int(a.polish))), flush=True)
        return
    a.output.mkdir(exist_ok=False)
    started = time.monotonic()
    me = [sys.executable, '-B', str(Path(__file__).resolve()), '--output', str(a.output)]
    jobs = [['--fixed', r, str(w)] for r in RANKINGS for w in WIDTHS] + [['--polish', str(s)] for s in v1.SIZES]
    log = []
    for job in jobs:
        t0 = time.monotonic()
        done = subprocess.run(me + job, capture_output=True, text=True)
        log.append({'job': job, 'returncode': done.returncode, 'seconds': time.monotonic() - t0, 'stderr_tail': done.stderr[-2000:]})
        print(json.dumps({'job': job, 'returncode': done.returncode, 'seconds': round(log[-1]['seconds'], 2)}), flush=True)
        if done.returncode:
            break
    write(a.output / 'run.json', {'schema': 'gamma.matched80.run.v2', 'jobs': log, 'elapsed_seconds': time.monotonic() - started,
                                  'host': platform.node(), 'python': platform.python_version(), 'platform': platform.platform(),
                                  'contract_sha256': sha((ROOT / 'contract.json').read_bytes()), 'runner_sha256': sha(Path(__file__).read_bytes()),
                                  'complete': all(j['returncode'] == 0 for j in log) and len(log) == len(jobs)})


if __name__ == '__main__':
    main()
