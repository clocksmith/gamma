"""Bounded flat-string learning with measured counterfactual segmentation gain.

Candidate frequency proposes a shortlist only. It never decides an admission.
All emitted source comes from counted strings; this is offline representation.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parent
PILOT = ROOT.parent
sys.path[:0] = [str(PILOT), str(PILOT / 'pass2/working')]
from literals import dictionary_bytes, pieces
from bitpack import encode, decode

spec = importlib.util.spec_from_file_location('cluster_search', PILOT / 'clusters-v1/search.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
segment = previous.encode_text
trie = previous.trie
ALPHABET = [chr(i) for i in range(32, 127)] + ['\n']
sha = lambda b: hashlib.sha256(b).hexdigest()


def sequences(texts, vocab):
    tree = trie(vocab)
    return {key: segment(text, tree) for key, text in texts.items()}


def exact_addition(texts, vocab, current, fragment):
    """Measure every occurrence together, including overlaps and resegmentation."""
    extended = vocab + [fragment]
    tree = trie(extended)
    changed = dict(current)
    for key, text in texts.items():
        if fragment in text:
            changed[key] = segment(text, tree)
    gain = sum(len(current[k]) - len(changed[k]) for k in texts)
    return gain, changed


def proposals(texts, vocab, current):
    counts, owners = Counter(), defaultdict(set)
    full = set(texts.values())
    for key, seq in current.items():
        strings = [vocab[i] for i in seq]
        for start in range(len(strings)):
            for size in (2, 3, 4):
                if start + size > len(strings):
                    break
                fragment = ''.join(strings[start:start + size])
                if len(fragment.encode()) <= 160 and fragment not in full:
                    counts[fragment] += size - 1
                    owners[fragment].add(key)
    return sorted((s for s in counts if len(owners[s]) >= 2 and s not in vocab),
                  key=lambda s: (-counts[s], len(s.encode()), s))


def static_vocabulary(texts, budget):
    """Matched old-style frequency ranking/truncation, with the same ASCII base."""
    counts, owners = Counter(), defaultdict(set)
    for key, text in texts.items():
        tokens = pieces(text, 'lexical')
        for start in range(len(tokens)):
            for size in range(1, 7):
                fragment = ''.join(tokens[start:start + size])
                if len(fragment) > 1 and len(fragment.encode()) <= 160 and fragment not in texts.values():
                    counts[fragment] += 1
                    owners[fragment].add(key)
    ranked = sorted((s for s in counts if len(owners[s]) >= 2),
                    key=lambda s: (-counts[s] * (len(s) - 1), len(s.encode()), s))
    return ALPHABET + ranked[:budget - len(ALPHABET)]


def learn(texts, limits):
    vocab = list(ALPHABET)
    current = sequences(texts, vocab)
    trace, snapshots, swaps = [], {}, []
    start, trials = time.monotonic(), 0
    # Reclaim learned entries made redundant by later additions. ASCII is retained.
    retired = set()
    for budget in (128, 256):
        while len(vocab) < budget and time.monotonic() - start < limits['search_seconds_per_arm']:
            candidates = [s for s in proposals(texts, vocab, current) if s not in retired][:limits['shortlist']]
            scored = []
            best = None
            for fragment in candidates:
                if trials >= limits['max_trials_per_arm'] or time.monotonic() - start >= limits['search_seconds_per_arm']:
                    break
                gain, proposed = exact_addition(texts, vocab, current, fragment)
                trials += 1
                scored.append({'literal': fragment, 'exact_selection_gain': gain})
                key = (-gain, len(fragment.encode()), fragment)
                if best is None or key < best[0]:
                    best = (key, fragment, proposed, gain)
            if best is None or best[3] <= 0:
                break
            _, chosen, proposed, gain = best
            before = sum(map(len, current.values()))
            vocab.append(chosen)
            current = proposed
            used = {i for seq in current.values() for i in seq}
            redundant = [i for i in range(len(ALPHABET), len(vocab)) if i not in used]
            retired.update(vocab[i] for i in redundant)
            if redundant:
                vocab = [s for i, s in enumerate(vocab) if i not in redundant]
                current = sequences(texts, vocab)
            after = sum(map(len, current.values()))
            assert before - after == gain
            trace.append({'step': len(trace), 'chosen': chosen, 'before': before, 'after': after,
                          'gain': gain, 'reclaimed_slots': len(redundant), 'entries': len(vocab), 'shortlist': scored})
            if len(trace) % 16 == 0:
                print(json.dumps({'phase':'admission','entries':len(vocab),'selections':after,'trials':trials}),flush=True)
        # A bounded swap compares complete dictionaries, not independent counts.
        frequency=Counter(i for seq in current.values() for i in seq)
        removals=sorted(range(len(ALPHABET),len(vocab)),key=lambda i:(frequency[i],-len(vocab[i]),vocab[i]))[:3]
        additions=proposals(texts,vocab,current)[:4]
        current_cost=(sum(map(len,current.values())),len(dictionary_bytes(vocab)))
        best_swap=None
        attempts=[]
        for remove in removals:
            for add in additions:
                if trials>=limits['max_trials_per_arm'] or time.monotonic()-start>=limits['search_seconds_per_arm']:break
                candidate=[s for k,s in enumerate(vocab) if k!=remove]+[add]
                proposed=sequences(texts,candidate);trials+=1
                cost=(sum(map(len,proposed.values())),len(dictionary_bytes(candidate)))
                attempts.append({'remove':vocab[remove],'add':add,'before_selections':current_cost[0],'after_selections':cost[0],'dictionary_bytes':cost[1]})
                if cost<current_cost and (best_swap is None or cost<best_swap[0]):best_swap=(cost,candidate,proposed,attempts[-1])
        if best_swap:
            _,vocab,current,decision=best_swap
        else:decision=None
        swaps.append({'budget':budget,'attempts':attempts,'accepted':decision})
        snapshots[budget] = (list(vocab), dict(current))
    return snapshots, {'steps': trace, 'exact_candidate_trials': trials, 'elapsed_seconds': time.monotonic()-start,
                       'swaps':swaps,'retired_literals': sorted(retired), 'time_limit_reached': time.monotonic()-start >= limits['search_seconds_per_arm']}


def save(folder, texts, vocab, seqs, width, arm, method):
    folder.mkdir(parents=True)
    raw = dictionary_bytes(vocab)
    (folder/'dictionary.ltd').write_bytes(raw)
    (folder/'dictionary.json').write_text(json.dumps(vocab, indent=2)+'\n')
    rows, counts, owners, packet_bytes, singles, single_bits = [], [], defaultdict(set), 0, 0, 0
    for key, text in texts.items():
        seq = seqs[key]
        packet = encode(vocab, seq, width)
        assert decode(raw, packet) == text
        (folder/f'{key}.ltv').write_bytes(packet)
        counts.append(len(seq)); packet_bytes += len(packet)
        singles += sum(len(vocab[i]) == 1 for i in seq)
        for i in seq: owners[i].add(key)
        rows.append({'id': int(key), 'source_sha256': sha(text.encode()), 'sequence': seq,
                     'packet_sha256': sha(packet), 'selections': len(seq), 'selection_bits': width*len(seq)})
    metrics = {'arm': arm, 'method': method, 'entries': len(vocab), 'bits_per_selection': width,
               'problems': len(texts), 'selections': sum(counts), 'selection_bits': width*sum(counts),
               'median_selections': statistics.median(counts), 'worst_selections': max(counts),
               'single_character_selections': singles, 'single_character_selection_fraction': singles/sum(counts),
               'cross_problem_literals': sum(len(v) >= 2 for v in owners.values()),
               'whole_program_literals': sum(s in texts.values() for s in vocab),
               'dictionary_bytes': len(raw), 'packet_bytes': packet_bytes, 'package_bytes': len(raw)+packet_bytes,
               'unused_entries': len(vocab)-len(owners), 'framing_bytes': 41*len(texts)}
    assert metrics['whole_program_literals'] == 0
    manifest = {'metrics': metrics, 'dictionary_sha256': sha(raw), 'programs': rows}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return metrics


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    contract=json.loads((ROOT/'contract.json').read_text())
    manifest=json.loads((ROOT/'generated/manifest.json').read_text())
    qualification=json.loads((ROOT/'qualification/report.json').read_text())
    assert all(r['passed'] for r in qualification['rows']) and qualification['source_count']==240
    assert qualification['generated_manifest_sha256']==sha((ROOT/'generated/manifest.json').read_bytes())
    a.output.mkdir(exist_ok=False)
    rows=[]
    for arm in ['canonical','compact']:
        texts={str(r['id']):(ROOT/'generated'/r['file']).read_text() for r in manifest['rows'] if r['variant']==arm}
        assert len(texts)==80
        for budget in (128,256):
            vocab=static_vocabulary(texts,budget)
            rows.append(save(a.output/f'{arm}-frequency-{budget}',texts,vocab,sequences(texts,vocab),budget.bit_length()-1,arm,'frequency-truncation'))
        snapshots,trace=learn(texts,contract['bounds'])
        (a.output/f'{arm}-trace.json').write_text(json.dumps(trace,indent=2)+'\n')
        for budget,(vocab,seqs) in snapshots.items():
            rows.append(save(a.output/f'{arm}-marginal-{budget}',texts,vocab,seqs,budget.bit_length()-1,arm,'counterfactual-resegmentation'))
        print(json.dumps({'arm':arm,'trials':trace['exact_candidate_trials'],'seconds':trace['elapsed_seconds'],'results':rows[-4:]}),flush=True)
    summary={'schema':'gamma.literal-scale-search.v2','rows':rows,'contract_sha256':sha((ROOT/'contract.json').read_bytes()),
             'source_manifest_sha256':sha((ROOT/'generated/manifest.json').read_bytes()),
             'qualification_sha256':sha((ROOT/'qualification/report.json').read_bytes()),
             'search_sha256':sha(Path(__file__).read_bytes()),'scope':'80 exposed development problems, supplied-code representation only; no fresh heldout evaluation.'}
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__=='__main__': main()
