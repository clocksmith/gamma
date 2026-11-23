#!/usr/bin/env python3
"""Source-free summary of fixed-source-v1: best results by cell, shared against
separate dictionaries, what the entries spell, and the frozen predictions.

    analyze.py <private folder> <run folder> <acorn.js>
"""
import bisect
import io
import json
import keyword
import subprocess
import sys
import tokenize
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify as V

GREEDY = ('greedy-entry', 'greedy-byte')
BASELINES = ('freq-occ', 'freq-doc', 'bpe', 'bpe-free')
NAMES = {'k': 'keyword', 'i': 'identifier', 'n': 'number', 's': 'string', 'c': 'comment',
         'p': 'punctuation', 't': 'indentation', 'l': 'newline', 'w': 'space'}


def python_classes(raw):
    text = raw.decode('latin1')
    marks = ['l' if ch in '\r\n' else 'w' for ch in text]
    starts = [0]
    for index, ch in enumerate(text):
        if ch == '\n':
            starts.append(index + 1)
    at = lambda position: starts[position[0] - 1] + position[1]
    def paint(start, end, letter):
        for index in range(at(start), at(end)):
            if text[index] not in '\r\n' or letter in 'sc':
                marks[index] = letter
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        kind = tokenize.tok_name[token.type]
        if kind == 'NAME':
            letter = 'k' if keyword.iskeyword(token.string) else 'i'
        elif kind == 'NUMBER':
            letter = 'n'
        elif kind in ('STRING', 'FSTRING_START', 'FSTRING_MIDDLE', 'FSTRING_END'):
            letter = 's'
        elif kind == 'COMMENT':
            letter = 'c'
        elif kind == 'OP':
            letter = 'p'
        else:
            continue
        paint(token.start, token.end, letter)
    line_start = True
    for index, mark in enumerate(marks):
        if mark == 'l':
            line_start = True
        elif line_start and mark == 'w':
            marks[index] = 't'
        else:
            line_start = False
    return ''.join(marks)


def dictionary(run, corpus, limit, budget, arm):
    if arm == 'greedy-polish':
        path = run / 'chains' / f'{corpus}-L{limit}-polish-K{budget}.txt'
        entries = V.read_chain(path)[0]
    else:
        entries = V.read_chain(run / 'chains' / f'{corpus}-L{limit}-{arm}.txt')[0]
        entries = entries[:V.prefix_for(entries, budget, None)]
    root = {}
    for row in entries:
        V.insert(root, row[4])
    return root, [row[4] for row in entries]


def attribution(docs, classes, root):
    saved, used = Counter(), defaultdict(lambda: [0, set()])
    uses = Counter()
    crossing = Counter()
    for index, raw in enumerate(docs):
        marks = classes[index]
        pieces = V.parse(raw, root)
        at = 0
        for piece in pieces:
            kinds = set(marks[at:at + len(piece)])
            at += len(piece)
            gain = len(piece) - 1
            uses[piece] += 1
            used[piece][0] += gain
            used[piece][1].add(index)
            if not gain:
                continue
            if len(kinds) == 1:
                saved[NAMES[next(iter(kinds))]] += gain
            else:
                saved['crosses a boundary'] += gain
                crossing[piece] += gain
    return saved, used, uses, crossing


def split_best(python, javascript, budget, cap):
    """The lowest total over every split of entries and stored bytes."""
    best = None
    head = 4 if cap is not None else 0
    jk = [row[0] for row in javascript]
    jb = [row[1] for row in javascript]
    for k_py, b_py, t_py in python:
        if t_py < 0 or k_py >= budget:
            continue
        left = budget - k_py
        room = None if cap is None else cap - head - b_py
        if room is not None and room <= 0:
            continue
        at = bisect.bisect_right(jk, left) - 1
        if room is not None:
            at = min(at, bisect.bisect_right(jb, room) - 1)
        if at < 0 or javascript[at][2] < 0:
            continue
        total = t_py + javascript[at][2]
        if best is None or total < best[0]:
            best = (total, k_py, javascript[at][0], b_py + javascript[at][1] + head)
    return best


def main():
    private, run, acorn = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    out = run / 'out'
    verified = json.loads((out / 'verification.json').read_text())
    chains = json.loads((out / 'chains.json').read_text())
    limits = json.loads((out / 'limits.json').read_text())
    files = V.load_corpus(private, Path(V.__file__).resolve().parent / 'manifest.json')
    rows = verified['rows']
    by = defaultdict(dict)
    for row in rows:
        by[(row['corpus'], row['L'], row['K'], row['B'])][row['arm']] = row
    table = []
    for (corpus, limit, budget, cap), arms in sorted(by.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3] or 10**9)):
        cell = {'corpus': corpus, 'L': limit, 'K': budget, 'B': cap, 'arms': {}}
        for arm, row in arms.items():
            value = {'entries': row['entries'], 'stored': row['stored_bytes'], 'spelled': row['spelled'],
                     'files': row['files'], 'emissions': row['emissions']}
            if 'ordinary_emissions' in row:
                value['ordinary'] = row['ordinary_emissions']
            cell['arms'][arm] = value
        table.append(cell)

    def emissions(corpus, limit, budget, arm, cap=None):
        row = by[(corpus, limit, budget, cap)].get(arm)
        return None if row is None else row['emissions']

    def best_found(corpus, limit, budget, cap=None):
        values = []
        for (c, l, k, b), arms in by.items():
            if c == corpus and l == limit and k <= budget and (cap is None or (b is not None and b <= cap)):
                values += [row['emissions'] for arm, row in arms.items()
                           if row['emissions'] is not None and (arm.startswith('greedy'))]
        return min(values) if values else None

    sharing = []
    for limit in (2, 4, 8, 16, 32, 64):
        for budget in V.GRID_K:
            for cap in V.GRID_B:
                shared = [emissions('both', limit, budget, arm, cap) for arm in GREEDY]
                shared = [x for x in shared if x is not None]
                options = []
                for a in GREEDY:
                    for b in GREEDY:
                        got = split_best(chains[f'python-L{limit}-{a}'], chains[f'javascript-L{limit}-{b}'], budget, cap)
                        if got:
                            options.append((*got, a, b))
                split = min(options) if options else None
                sharing.append({'L': limit, 'K': budget, 'B': cap, 'shared': min(shared) if shared else None,
                                'separate': split[0] if split else None, 'python_entries': split[1] if split else None,
                                'javascript_entries': split[2] if split else None,
                                'separate_stored': split[3] if split else None,
                                'python_arm': split[4] if split else None, 'javascript_arm': split[5] if split else None})
    # Rebuild and decode the separate dictionaries behind the headline cells.
    decoded = 0
    for row in sharing:
        if row['separate'] is None or row['L'] != 16 or row['B'] is not None:
            continue
        total = 0
        for language, key, arm in (('python', 'python_entries', 'python_arm'), ('javascript', 'javascript_entries', 'javascript_arm')):
            entries = V.read_chain(run / 'chains' / f'{language}-L16-{row[arm]}.txt')[0][:row[key]]
            root = {}
            for item in entries:
                V.insert(root, item[4])
            spelled, tokens = V.score(files[language], root)
            if spelled != 400:
                raise SystemExit('a separate dictionary did not spell its language')
            total += tokens
        if total != row['separate']:
            raise SystemExit('separate total differs from its decode')
        decoded += 1

    lists = {name: (private / 'lists' / f'{name}.txt').read_text().split() for name in ('javascript',)}
    js_marks = json.loads(subprocess.run(['node', str(Path(V.__file__).resolve().parent / 'lex.cjs'), acorn,
                                          str(private / 'lists' / 'javascript.txt')], capture_output=True, check=True).stdout)
    classes = {'python': [python_classes(raw) for raw in files['python']],
               'javascript': [js_marks[path] for path in lists['javascript']]}
    classes['both'] = classes['python'] + classes['javascript']
    for name in ('python', 'javascript'):
        for raw, marks in zip(files[name], classes[name]):
            if len(raw) != len(marks):
                raise SystemExit('class map length differs from source')
    profile = {'source_bytes': {}, 'by_budget': {}}
    for name in ('python', 'javascript', 'both'):
        profile['source_bytes'][name] = {NAMES[k]: v for k, v in Counter(''.join(classes[name])).items()}
    private_examples = {}
    for budget in (256, 1024):
        for name in ('python', 'javascript', 'both'):
            arm = 'greedy-polish' if by[(name, 16, budget, None)].get('greedy-polish', {}).get('emissions') else 'greedy-entry'
            root, entries = dictionary(run, name, 16, budget, arm)
            saved, used, uses, crossing = attribution(files[name], classes[name], root)
            total = sum(saved.values())
            multi = [e for e in entries if len(e) > 1]
            docs_used = sorted((len(used[e][1]) for e in multi if e in used), reverse=True)
            row = {'arm': arm, 'entries': len(entries), 'multi_byte_entries': len(multi),
                   'saved_by_kind': dict(saved), 'saved_total': total,
                   'crossing_share': saved['crosses a boundary'] / total if total else 0,
                   'median_files_per_multibyte_entry': docs_used[len(docs_used) // 2] if docs_used else 0,
                   'multibyte_entries_never_used': sum(1 for e in multi if e not in used)}
            if name == 'both':
                py_docs = 400
                only_py = only_js = in_both = 0
                saved_py = saved_js = saved_both = 0
                for entry in multi:
                    if entry not in used:
                        continue
                    who = used[entry][1]
                    a, b = any(i < py_docs for i in who), any(i >= py_docs for i in who)
                    if a and b:
                        in_both += 1; saved_both += used[entry][0]
                    elif a:
                        only_py += 1; saved_py += used[entry][0]
                    else:
                        only_js += 1; saved_js += used[entry][0]
                row['entries_used_by'] = {'both': in_both, 'python_only': only_py, 'javascript_only': only_js}
                row['saved_by_user'] = {'both': saved_both, 'python_only': saved_py, 'javascript_only': saved_js}
            profile['by_budget'][f'{name}-K{budget}'] = row
            top = sorted(((used[e][0], len(used[e][1]), e.decode('latin1')) for e in multi if e in used), reverse=True)[:40]
            cross = [(gain, piece.decode('latin1')) for piece, gain in crossing.most_common(40)]
            private_examples[f'{name}-K{budget}'] = {'top_entries': top, 'top_crossing': cross}
    (out / 'private-examples.json').write_text(json.dumps(private_examples, indent=1))

    bpe16 = by[('both', 16, 256, None)]
    base = [bpe16[a]['emissions'] for a in BASELINES]
    greedy = bpe16['greedy-entry']['emissions']
    bpe_short, bpe_ord = bpe16['bpe']['emissions'], bpe16['bpe']['ordinary_emissions']
    share = {(r['K']): r for r in sharing if r['L'] == 16 and r['B'] is None}
    feasible = [k for k in V.GRID_K if k <= 1024 and share[k]['shared'] is not None]
    p3 = all(share[k]['separate'] is None or share[k]['shared'] < share[k]['separate'] for k in feasible)
    crossing = profile['by_budget']['both-K256']['crossing_share']
    predictions = {
        'P1': {'text': 'greedy at least 5% below the best baseline at K=256, L=16, both',
               'greedy': greedy, 'best_baseline': min(base), 'reduction': 1 - greedy / min(base),
               'held': greedy <= 0.95 * min(base)},
        'P2': {'text': 'shortest-path parsing lowers BPE by at least 3% at that cell',
               'ordinary': bpe_ord, 'shortest': bpe_short, 'reduction': 1 - bpe_short / bpe_ord,
               'held': bpe_short <= 0.97 * bpe_ord},
        'P3': {'text': 'shared beats separate at every K up to 1024, L=16, uncapped',
               'cells': {k: [share[k]['shared'], share[k]['separate']] for k in feasible}, 'held': p3},
        'P4': {'text': 'separate beats shared at K=4096, L=16',
               'shared': share[4096]['shared'], 'separate': share[4096]['separate'],
               'held': share[4096]['separate'] < share[4096]['shared']},
        'P5': {'text': 'no-singleton cannot spell all 800 at any K, L=16, proved by reachability',
               'spellable': limits['corpora']['both']['no_singleton']['16']['spellable_files'],
               'held': limits['corpora']['both']['no_singleton']['16']['spellable_files'] < 800},
        'P6': {'text': 'no dictionary below the alphabet spells a whole corpus, by block rank',
               'ranks': {c: [v['block_rank'], v['alphabet']] for c, v in limits['corpora'].items()},
               'held': all(max(v['block_rank']) == v['alphabet'] for v in limits['corpora'].values())},
        'P7': {'text': 'entries crossing a lexical boundary save more than half at K=256, L=16, both',
               'share': crossing, 'held': crossing > 0.5},
    }
    summary = {'schema': 'gamma.fixed-source-summary.v1', 'chains': verified['chains'], 'cells': verified['cells'],
               'polished_dictionaries': verified.get('polished_dictionaries'), 'stopped_chains': verified['stopped_chains'],
               'separate_splits_decoded': decoded, 'limits': limits, 'predictions': predictions,
               'sharing': sharing, 'profile': profile, 'table': table}
    (out / 'summary.json').write_text(json.dumps(summary, separators=(',', ':')) + '\n')
    for key, value in predictions.items():
        print(key, 'HELD' if value['held'] else 'FAILED', {k: v for k, v in value.items() if k not in ('text', 'held', 'cells', 'ranks')})


if __name__ == '__main__':
    main()
