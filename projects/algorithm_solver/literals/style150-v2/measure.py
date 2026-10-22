"""style150-v2: rerun the style150-v1 search arms with the proposer fixed (contract.json).

The only change from style150-v1/measure.py: candidate spans are scored on each problem's
currently chosen source only, not on every variant in the pool. In style150-v1 the joint-v1
span proposer counted unchosen verbose variants, so its shortlist filled with whitespace
runs that save nothing and the mixed-pool and from-alphabet searches stopped early.

  measure.py --work DIR --output DIR/style150/run-v2 [--parallel N]
"""
import argparse, concurrent.futures, hashlib, importlib.util, json, os, sys, time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
spec = importlib.util.spec_from_file_location('style150_v1_measure', LIT / 'style150-v1/measure.py')
m1 = importlib.util.module_from_spec(spec); sys.path.insert(0, str(LIT / 'style150-v1')); spec.loader.exec_module(m1)
v3, joint, v1, write = m1.v3, m1.joint, m1.v1, m1.write


def proposals_chosen(sources, state, limit):
    """joint-v1 proposals(), restricted to each problem's chosen source."""
    scores, owners = defaultdict(dict), defaultdict(set)
    full = {t for vs in sources.values() for t in vs.values()}
    for pid, variant in state['chosen'].items():
        parts = state['parsed'][(pid, variant)]
        counts = Counter()
        for start in range(len(parts)):
            for length in range(2, 7):
                if start + length > len(parts): break
                fragment = ''.join(parts[start:start + length])
                if len(fragment.encode()) <= 160 and fragment not in full and fragment not in state['vocab']:
                    counts[fragment] += length - 1
        for fragment, score in counts.items():
            scores[fragment][pid] = max(score, scores[fragment].get(pid, 0)); owners[fragment].add(pid)
    return sorted((s for s in scores if len(owners[s]) >= 2), key=lambda s: (-sum(scores[s].values()), len(s.encode()), s))[:limit]


def hybrid_chosen(designed_all, sources):
    """matched80-v3 hybrid_proposer with proposals_chosen in place of joint.proposals."""
    owners = lambda s: sum(any(s in t for t in variants.values()) for variants in sources.values())
    witnessed = [s for s in dict.fromkeys(designed_all) if owners(s) >= 2]
    def propose(sources, state, limit, fraction):
        slots = int(limit * fraction)
        mined = proposals_chosen(sources, state, 10 ** 9)
        head = mined[:limit - slots]
        present = set(state['vocab']) | set(head)
        chosen = '\x00'.join(sources[pid][v] for pid, v in sorted(state['chosen'].items()))
        ranked = v1.rank([s for s in witnessed if s not in present], chosen, state['vocab'])[:slots]
        rest = [s for s in mined[len(head):] if s not in ranked]
        return head + ranked + rest[:limit - len(head) - len(ranked)]
    return propose


def contract():
    c = json.loads((HERE / 'contract.json').read_text())
    for rel, h in c['code_hashes'].items(): assert sha((LIT / rel).read_bytes()) == h, rel
    c1 = m1.contract(); assert sha((LIT / 'style150-v1/contract.json').read_bytes()) == c['style150_v1_contract_sha256']
    return {**c1, 'search': c['search'], 'arms2': c['arms']}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--parallel', type=int, default=16)
    a = ap.parse_args(); c = contract(); a.output.mkdir(parents=True, exist_ok=False)
    v3.hybrid_proposer = hybrid_chosen  # the single change; style150-v1's run_arm calls v3.hybrid_proposer
    jobs = [j for j in m1.jobs(a.work.resolve(), a.output.resolve(), c, None) if j['name'].split('-')[0] in c['arms2']]
    start = time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(a.parallel, initializer=_patch) as pool:
        results = list(pool.map(run, jobs))
    write(a.output / 'results.json', {'contract_sha256': sha((HERE / 'contract.json').read_bytes()), 'seconds': time.monotonic() - start, 'arms': results})
    for r in results:
        s = r['all150']
        print(f"{r['arm']:8} sel {s['selections']:6} med {s['median']:6} p95 {s['p95']:4} char {s['single_character_selection_fraction']:.3f} pkg {r['package_bytes']} entries {r['entries']} trials {r['trials']} {r['stop']}"
              + (f" | heldout {r['heldout30']['selections']}" if 'heldout30' in r else ''))


def _patch():
    v3.hybrid_proposer = hybrid_chosen


def run(job):
    """Picklable worker entry (the v1 module is loaded dynamically and cannot be pickled by reference)."""
    _patch()
    return m1.run_arm(job)


if __name__ == '__main__':
    main()
