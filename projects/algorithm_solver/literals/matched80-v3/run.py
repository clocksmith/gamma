"""Iteration 3 on the 80 sources: wide hybrid polish, seeded iterated local search, and readable units.

Literal arms search the 80 compact sources (the published BITS cohort) with the
matched80-v1 codec, fallback, scoring and verification. Readable arms admit only
readable-units-v1 units and approved designed pieces and keep their own scorecard.
Every budget, seed and neighborhood size comes from contract.json. Nothing executes
candidate source; every packet must decode, through the canonical codec, to a
qualified source hash.
"""
import argparse
import importlib.util
import json
import os
import platform
import random
import subprocess
import sys
import time
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIT = ROOT.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


v1 = module('matched80_v1', LIT / 'matched80-v1/run.py')
units = module('readable_units', ROOT / 'units.py')
base, joint, sha, write = v1.base, v1.joint, v1.sha, v1.write
FALLBACK = set(base.ALPHABET)
SIZES = (128, 256)
STARTS = {'v2polish': 'matched80-v2/run-v1/polish-{size}/dictionary.json',
          'scalev2': 'scale-v2/search-v2/compact-marginal-{size}/dictionary.json'}
cost = lambda state: (state['selections'], state['package_bytes'])


class Budget:
    """Trial cap binds; the time cap is a safety limit that is flagged when reached."""
    def __init__(self, limits):
        self.cap, self.seconds, self.trials, self.start = limits['trials'], limits['seconds'], 0, time.monotonic()

    def expired(self):
        return self.trials >= self.cap or time.monotonic() - self.start >= self.seconds

    def reason(self):
        return 'trial_limit' if self.trials >= self.cap else 'time_limit'

    def elapsed(self):
        return time.monotonic() - self.start


def evaluate(sources, vocab, width, parent, budget, relaxed=False):
    budget.trials += 1
    return joint.evaluate(sources, vocab, width + relaxed, parent)


def prune(sources, state, width, budget):
    pruned, removed = joint.prune(sources, state, width)
    budget.trials += bool(removed)
    return pruned, removed


def hybrid_proposer(designed_all, sources):
    """3/4 of the additions in joint-v1 span order, 1/4 designed pieces ranked by the matched80-v1 estimator."""
    owners = lambda s: sum(any(s in t for t in variants.values()) for variants in sources.values())
    witnessed = [s for s in dict.fromkeys(designed_all) if owners(s) >= 2]
    def propose(sources, state, limit, fraction):
        slots = int(limit * fraction)
        mined = joint.proposals(sources, state, 10**9)
        head = mined[:limit - slots]
        present = set(state['vocab']) | set(head)
        chosen = '\x00'.join(sources[pid][v] for pid, v in sorted(state['chosen'].items()))
        ranked = v1.rank([s for s in witnessed if s not in present], chosen, state['vocab'])[:slots]
        rest = [s for s in mined[len(head):] if s not in ranked]
        return head + ranked + rest[:limit - len(head) - len(ranked)]
    return propose


def readable_proposer(pool):
    """Only readable pool members, ranked by the matched80-v1 estimator (span ranking does not apply)."""
    def propose(sources, state, limit, fraction=None):
        present = set(state['vocab'])
        chosen = '\x00'.join(sources[pid][v] for pid, v in sorted(state['chosen'].items()))
        return v1.rank([s for s in pool if s not in present], chosen, state['vocab'])[:limit]
    return propose


def best_move(sources, state, width, propose, nb, budget):
    """Exact deletion harm and addition gain screen swaps and double swaps; the best exact move wins."""
    vocab = set(state['vocab'])
    learned = [s for s in state['vocab'] if s not in FALLBACK]
    found, move, tested = None, None, set()

    def consider(remove=(), add=(), relaxed=False):
        nonlocal found, move
        candidate = (vocab - set(remove)) | set(add)
        identity = (tuple(sorted(candidate)), relaxed)
        if identity in tested or budget.expired() or (not relaxed and len(candidate) > 2**width):
            return None
        tested.add(identity)
        result = evaluate(sources, candidate, width, state, budget, relaxed)
        if not relaxed and cost(result) < cost(found or state):
            found, move = result, {'remove': list(remove), 'add': list(add)}
        return result

    harm = {}
    for fragment in learned:
        result = consider(remove=[fragment])
        if result:
            harm[fragment] = result['selections'] - state['selections']
    room = len(vocab) < 2**width
    gain = {}
    for fragment in propose(sources, state, nb['additions'], nb['designed_fraction']):
        result = consider(add=[fragment], relaxed=not room)
        if result:
            gain[fragment] = state['selections'] - result['selections']
    swaps = sorted(((gain[a] - harm[r], r, a) for r in harm for a in gain), key=lambda x: (-x[0], x[1], x[2]))
    for _, remove, add in swaps[:nb['swaps']]:
        consider(remove=[remove], add=[add])
    top = sorted(gain, key=lambda a: (-gain[a], a))[:nb['pair_additions']]
    low = sorted(harm, key=lambda r: (harm[r], r))[:nb['pair_removals']]
    need = max(0, len(vocab) + 2 - 2**width)
    doubles = sorted(((gain[a] + gain[b] - sum(harm[r] for r in rem), rem, (a, b))
                      for a, b in combinations(top, 2) for rem in combinations(low, need)), key=lambda x: (-x[0], x[1], x[2]))
    for _, remove, add in doubles[:nb['pairs']]:
        consider(remove=remove, add=add)
    return found, move


def local_search(sources, state, width, propose, nb, budget, log):
    while not budget.expired():
        found, move = best_move(sources, state, width, propose, nb, budget)
        if found is None:
            return state, budget.reason() if budget.expired() else 'local_optimum'
        state, pruned = prune(sources, found, width, budget)
        log.append({'move': move, 'pruned': pruned, 'after': joint.brief(state), 'trials': budget.trials})
    return state, budget.reason()


def refill(sources, state, width, propose, nb, limit, budget):
    """Greedy exact refill after a kick: best measured addition from the shortlist until full or no gain."""
    added = []
    while len(state['vocab']) < 2**width and not budget.expired():
        best = None
        for fragment in propose(sources, state, limit, nb['designed_fraction']):
            if budget.expired():
                break
            result = evaluate(sources, set(state['vocab']) | {fragment}, width, state, budget)
            if result['selections'] < state['selections'] and (best is None or cost(result) < cost(best[0])):
                best = (result, fragment)
        if best is None:
            break
        state, _ = prune(sources, best[0], width, budget)
        added.append(best[1])
    return state, added


def iterated(sources, start, width, propose, nb, kick, seed, budget):
    """Seeded kicks (remove `kick` learned entries uniformly), greedy refill, local search; keep only improvements."""
    rng, incumbent, kicks = random.Random(seed), start, []
    while not budget.expired():
        learned = sorted(s for s in incumbent['vocab'] if s not in FALLBACK)
        removed = rng.sample(learned, kick)
        state, _ = prune(sources, evaluate(sources, set(incumbent['vocab']) - set(removed), width, incumbent, budget), width, budget)
        state, added = refill(sources, state, width, propose, nb, nb['refill_shortlist'], budget)
        log = []
        state, stop = local_search(sources, state, width, propose, nb, budget, log)
        accepted = cost(state) < cost(incumbent)
        kicks.append({'removed': removed, 'refilled': added, 'rounds': len(log), 'result': joint.brief(state),
                      'accepted': accepted, 'stop': stop, 'trials': budget.trials})
        if accepted:
            incumbent = state
    return incumbent, kicks


def contract():
    value = json.loads((ROOT / 'contract.json').read_text())
    for rel, digest in value['inputs'].items():
        if sha((ROOT / rel).read_bytes()) != digest:
            raise ValueError(f'frozen input changed: {rel}')
    return value


def inputs():
    c1 = json.loads((LIT / 'matched80-v1/contract.json').read_text())
    texts, metadata = v1.load_inputs(c1)
    designed = v1.designed_pool(c1)
    return texts, metadata, designed


def save(out, name, sources, metadata, state, width, method, provenance, extra):
    folder = out / name
    joint.save(folder, sources, metadata, state, width, method)
    chosen = {str(pid): sources[pid][v] for pid, v in state['chosen'].items()}
    return v1.verify_and_extend(folder, chosen, state['vocab'], provenance, extra)


def run_wide(c, out, start, size):
    texts, metadata, designed = inputs()
    sources = {int(pid): {'compact': text} for pid, text in texts['compact'].items()}
    width = size.bit_length() - 1
    designed_all = designed['canonical'] + designed['compact']
    budget = Budget(c['wide'])
    vocab = json.loads((LIT / STARTS[start].format(size=size)).read_text())
    initial, _ = prune(sources, evaluate(sources, vocab, width, None, budget), width, budget)
    log = []
    final, stop = local_search(sources, initial, width, hybrid_proposer(designed_all, sources), c['neighborhood'], budget, log)
    name = f'wide-{start}-{size}'
    write(out / f'{name}-trace.json', {'start': start, 'initial': joint.brief(initial), 'rounds': log, 'stop': stop})
    met = save(out, name, sources, metadata, final, width, 'wide-hybrid-polish', v1.provenance_of(designed_all),
               {'kind': 'wide', 'size': size, 'start': start, 'start_selections': initial['selections']})
    write(out / f'{name}-resources.json', {'search_seconds': budget.elapsed(), 'trials': budget.trials, 'stop': stop,
                                           'rounds': len(log), **v1.peak_memory()})
    return met


def run_ils(c, out, size, seed):
    texts, metadata, designed = inputs()
    sources = {int(pid): {'compact': text} for pid, text in texts['compact'].items()}
    width = size.bit_length() - 1
    designed_all = designed['canonical'] + designed['compact']
    starts = [(json.loads((out / f'wide-{s}-{size}/manifest.json').read_text())['metrics'], f'wide-{s}-{size}') for s in STARTS]
    best_metrics, best_name = min(starts, key=lambda a: (a[0]['selections'], a[0]['package_bytes'], a[1]))
    budget = Budget(c['ils'])
    vocab = json.loads((out / best_name / 'dictionary.json').read_text())
    start, _ = prune(sources, evaluate(sources, vocab, width, None, budget), width, budget)
    nb = {**c['neighborhood'], 'refill_shortlist': c['ils']['refill_shortlist']}
    final, kicks = iterated(sources, start, width, hybrid_proposer(designed_all, sources), nb, c['ils']['kick'][str(size)], seed, budget)
    assert cost(final) <= cost(start)
    name = f'ils-{size}-s{seed}'
    write(out / f'{name}-trace.json', {'start_arm': best_name, 'seed': seed, 'initial': joint.brief(start), 'kicks': kicks})
    met = save(out, name, sources, metadata, final, width, 'seeded-iterated-local-search', v1.provenance_of(designed_all),
               {'kind': 'ils', 'size': size, 'seed': seed, 'start_arm': best_name, 'start_selections': start['selections']})
    write(out / f'{name}-resources.json', {'search_seconds': budget.elapsed(), 'trials': budget.trials, 'stop': budget.reason(),
                                           'kicks': len(kicks), 'accepted_kicks': sum(k['accepted'] for k in kicks), **v1.peak_memory()})
    return met


def readable_pool(texts, designed, pool, style):
    found = units.extract(texts[style])
    classes = dict(found)
    if pool == 'units-designed':
        for text in designed[style]:
            classes.setdefault(text, 'designed')
    return classes


def run_readable(c, out, pool, style):
    texts, metadata, designed = inputs()
    classes = readable_pool(texts, designed, pool, style)
    members = sorted(classes)
    sources = {int(pid): {style: text} for pid, text in texts[style].items()}
    r = c['readable']
    def learn_propose(texts_, vocab, current, retired):
        present = set(vocab) | retired
        return v1.rank([s for s in members if s not in present], '\x00'.join(texts_.values()), vocab)
    snapshots, trace = v1.learn(texts[style], r['learn'], learn_propose)
    write(out / f'readable-{pool}-{style}-learn-trace.json', trace)
    provenance = lambda s: 'fallback' if s in FALLBACK else classes[s]
    rows = []
    for size, (vocab, _) in snapshots.items():
        width = size.bit_length() - 1
        budget = Budget(r['polish'])
        initial, _ = prune(sources, evaluate(sources, vocab, width, None, budget), width, budget)
        log = []
        final, stop = local_search(sources, initial, width, readable_proposer(members), c['neighborhood'], budget, log)
        assert set(final['vocab']) <= FALLBACK | set(members), 'readable policy violated'
        name = f'readable-{pool}-{style}-{size}'
        write(out / f'{name}-trace.json', {'initial': joint.brief(initial), 'rounds': log, 'stop': stop})
        aligned = [units.aligned_fraction(sources[pid][v], final['parsed'][(pid, v)]) * len(final['parsed'][(pid, v)])
                   for pid, v in final['chosen'].items()]
        met = save(out, name, sources, metadata, final, width, f'readable-units-v1-{pool}', provenance,
                   {'kind': 'readable', 'pool': pool, 'style': style, 'size': size, 'pool_size': len(members),
                    'learn_selections': initial['selections'], 'token_aligned_selection_fraction': sum(aligned) / final['selections']})
        write(out / f'{name}-resources.json', {'search_seconds': budget.elapsed() + trace['elapsed_seconds'], 'learn_seconds': trace['elapsed_seconds'],
                                               'trials': budget.trials + trace['exact_candidate_trials'], 'learn_trials': trace['exact_candidate_trials'],
                                               'stop': stop, 'rounds': len(log), **v1.peak_memory()})
        rows.append(met)
    return rows


def jobs_for(c):
    wide = [['--wide', s, str(size)] for size in SIZES for s in STARTS]
    readable = [['--readable', p, s] for p in c['readable']['pools'] for s in c['readable']['styles']]
    ils = [['--ils', str(size), str(seed)] for size in SIZES for seed in c['ils']['seeds']]
    return wide, readable, ils


def orchestrate(c, out, parallel):
    """Wide and readable jobs start together; each size's seeds start once both of its wide starts finish."""
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    me = [sys.executable, '-B', str(Path(__file__).resolve()), '--output', str(out)]
    env = {**os.environ, 'PYTHONHASHSEED': '0'}
    wide, readable, ils = jobs_for(c)
    queue, running, log = wide + readable, {}, []
    pending_ils = {size: [j for j in ils if j[1] == str(size)] for size in SIZES}
    done_wide = {size: 0 for size in SIZES}
    while queue or running or any(pending_ils.values()):
        while queue and len(running) < parallel:
            job = queue.pop(0)
            running[tuple(job)] = (subprocess.Popen(me + job, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env), time.monotonic())
        time.sleep(1)
        for key, (proc, t0) in list(running.items()):
            if proc.poll() is None:
                continue
            stdout, stderr = proc.communicate()
            del running[key]
            log.append({'job': list(key), 'returncode': proc.returncode, 'seconds': time.monotonic() - t0, 'stderr_tail': stderr[-2000:]})
            print(json.dumps({'job': list(key), 'returncode': proc.returncode, 'seconds': round(log[-1]['seconds'], 1)}), flush=True)
            if proc.returncode:
                for other, _ in running.values():
                    other.kill()
                queue, running, pending_ils = [], {}, {}
                break
            if key[0] == '--wide':
                size = int(key[2])
                done_wide[size] += 1
                if done_wide[size] == len(STARTS):
                    queue += pending_ils.pop(size)
    total = sum(map(len, jobs_for(c)))
    write(out / 'run.json', {'schema': 'gamma.matched80.run.v3', 'jobs': log, 'elapsed_seconds': time.monotonic() - started,
                             'host': platform.node(), 'python': platform.python_version(), 'platform': platform.platform(),
                             'parallel': parallel, 'contract_sha256': sha((ROOT / 'contract.json').read_bytes()),
                             'runner_sha256': sha(Path(__file__).read_bytes()),
                             'complete': len(log) == total and all(j['returncode'] == 0 for j in log)})


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--wide', nargs=2, metavar=('START', 'SIZE'))
    p.add_argument('--ils', nargs=2, metavar=('SIZE', 'SEED'))
    p.add_argument('--readable', nargs=2, metavar=('POOL', 'STYLE'))
    p.add_argument('--parallel', type=int, default=4)
    a = p.parse_args()
    c = contract()
    if a.wide:
        print(json.dumps(run_wide(c, a.output, a.wide[0], int(a.wide[1]))), flush=True)
    elif a.ils:
        print(json.dumps(run_ils(c, a.output, int(a.ils[0]), int(a.ils[1]))), flush=True)
    elif a.readable:
        print(json.dumps(run_readable(c, a.output, *a.readable)), flush=True)
    else:
        orchestrate(c, a.output, a.parallel)


if __name__ == '__main__':
    main()
