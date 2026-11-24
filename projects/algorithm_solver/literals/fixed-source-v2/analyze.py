#!/usr/bin/env python3
"""Source-free summary of fixed-source-v2: frozen endpoints and predictions, the
primary policy against its controls, shared against separate dictionaries, and
what the entries spell. Private examples stay in the private run folder.

    analyze.py <v1 private folder> <run folder> <acorn.js>
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

PRIMARY, ISOLATION, CONTROL = 's1-whole', 's1-nowhole', 's2-nowhole'
GREEDY = ('greedy-entry', 'greedy-byte')
BEST = ('greedy-entry', 'greedy-byte', 'greedy-polish')
BASELINES = ('freq-occ', 'freq-doc', 'bpe')
CORPORA = ('python', 'javascript', 'both')
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


def chain_path(run, policy, corpus, limit, arm, budget=None):
    name = f'{corpus}-L{limit}-polish-K{budget}.txt' if arm == 'greedy-polish' else f'{corpus}-L{limit}-{arm}.txt'
    return run / 'chains' / policy / name


def dictionary(run, policy, corpus, limit, budget, arm):
    entries = V.read_chain(chain_path(run, policy, corpus, limit, arm, budget))[1]
    if arm != 'greedy-polish':
        entries = entries[:V.prefix_for(entries, budget, None)]
    root = {}
    for row in entries:
        V.insert(root, row[4])
    return root, [row[4] for row in entries]


def attribution(docs, classes, root, one_file):
    saved, used, crossing = Counter(), defaultdict(lambda: [0, set()]), Counter()
    one_file_saved = 0
    for index, raw in enumerate(docs):
        marks, at = classes[index], 0
        for piece in V.parse(raw, root):
            kinds = set(marks[at:at + len(piece)])
            at += len(piece)
            gain = len(piece) - 1
            used[piece][0] += gain
            used[piece][1].add(index)
            if not gain:
                continue
            if piece in one_file:
                one_file_saved += gain
            if len(kinds) == 1:
                saved[NAMES[next(iter(kinds))]] += gain
            else:
                saved['crosses a boundary'] += gain
                crossing[piece] += gain
    return saved, used, crossing, one_file_saved


def split_best(python, javascript, budget, cap):
    """The lowest total over every split of entries and stored bytes."""
    best = None
    head = 4 if cap is not None else 0
    jk = [row[0] for row in javascript]
    jb = [row[1] for row in javascript]
    for k_py, b_py, t_py in python:
        if t_py < 0 or k_py >= budget:
            continue
        room = None if cap is None else cap - head - b_py
        if room is not None and room <= 0:
            continue
        at = bisect.bisect_right(jk, budget - k_py) - 1
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
    census = json.loads((out / 'census.json').read_text())['corpora']
    reach = json.loads((out / 'reachability.json').read_text())['corpora']
    regression = json.loads((out / 'regression.json').read_text())
    files = V.load_corpus(private)
    by = defaultdict(dict)
    for row in verified['rows']:
        by[(row['policy'], row['corpus'], row['L'], row['K'], row['B'])][row['arm']] = row

    # The isolation policy must differ from the primary by exactly the census strings.
    collapse = []
    meta = verified['chain_meta']
    for corpus in CORPORA:
        for limit in (2, 4, 8, 16, 32, 64):
            expected = census[corpus]['by_L'][str(limit)]['whole_file_strings_within_L']
            primary = meta[f'{PRIMARY}/{corpus}-L{limit}-greedy-entry']['candidates']
            key = f'{ISOLATION}/{corpus}-L{limit}-greedy-entry'
            if key in meta:
                difference = primary - meta[key]['candidates']
                if difference != expected:
                    raise SystemExit(f'census differs from candidates at {corpus} L={limit}')
            elif expected:
                raise SystemExit(f'isolation run missing at {corpus} L={limit}')
            else:
                difference = 0
            collapse.append({'corpus': corpus, 'L': limit, 'whole_file_strings': expected,
                             'candidate_difference': difference, 'isolation_ran': key in meta,
                             'primary_candidates': primary,
                             'control_candidates': meta[f'{CONTROL}/{corpus}-L{limit}-greedy-entry']['candidates']})

    table = []
    for (policy, corpus, limit, budget, cap), arms in sorted(by.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[0][4] or 10**9)):
        cell = {'policy': policy, 'corpus': corpus, 'L': limit, 'K': budget, 'B': cap, 'arms': {}}
        for arm, row in arms.items():
            value = {'entries': row['entries'], 'stored': row['stored_bytes'], 'spelled': row['spelled'], 'files': row['files'],
                     'emissions': row['emissions'], 'one_file_entries': row['one_file_entries'],
                     'whole_file_entries': row['whole_file_entries'], 'one_file_tokens': row['one_file_tokens'],
                     'whole_file_tokens': row['whole_file_tokens']}
            if 'ordinary_emissions' in row:
                value['ordinary'] = row['ordinary_emissions']
            cell['arms'][arm] = value
        table.append(cell)

    def cell(policy, corpus, limit, budget, cap=None):
        return by.get((policy, corpus, limit, budget, cap), {})

    def best(policy, corpus, limit, budget, cap=None):
        rows = [(cell(policy, corpus, limit, budget, cap)[arm]['emissions'], order, arm)
                for order, arm in enumerate(BEST) if arm in cell(policy, corpus, limit, budget, cap)
                and cell(policy, corpus, limit, budget, cap)[arm]['emissions'] is not None]
        return min(rows) if rows else None

    def best_value(policy, corpus, limit, budget, cap=None):
        found = best(policy, corpus, limit, budget, cap)
        return None if found is None else found[0]

    def coverage(policy, budget, cap=None, limit=16, corpus='both'):
        return cell(policy, corpus, limit, budget, cap)['cover-nosingle']['spelled']

    sharing = []
    for policy in (PRIMARY, CONTROL):
        for limit in (2, 4, 8, 16, 32, 64):
            for budget in V.GRID_K:
                for cap in V.GRID_B:
                    shared = [cell(policy, 'both', limit, budget, cap)[arm]['emissions'] for arm in GREEDY]
                    shared = [x for x in shared if x is not None]
                    options = []
                    for a in GREEDY:
                        for b in GREEDY:
                            got = split_best(chains[f'{policy}/python-L{limit}-{a}'], chains[f'{policy}/javascript-L{limit}-{b}'], budget, cap)
                            if got:
                                options.append((*got, a, b))
                    split = min(options) if options else None
                    sharing.append({'policy': policy, 'L': limit, 'K': budget, 'B': cap, 'shared': min(shared) if shared else None,
                                    'separate': split[0] if split else None, 'python_entries': split[1] if split else None,
                                    'javascript_entries': split[2] if split else None, 'separate_stored': split[3] if split else None,
                                    'python_arm': split[4] if split else None, 'javascript_arm': split[5] if split else None})

    js_list = (private / 'lists' / 'javascript.txt').read_text().split()
    js_marks = json.loads(subprocess.run(['node', str(private / 'lex.cjs'), acorn, str(private / 'lists' / 'javascript.txt')],
                                         capture_output=True, check=True).stdout)
    classes = {'python': [python_classes(raw) for raw in files['python']], 'javascript': [js_marks[path] for path in js_list]}
    classes['both'] = classes['python'] + classes['javascript']
    for name in ('python', 'javascript'):
        for raw, marks in zip(files[name], classes[name]):
            if len(raw) != len(marks):
                raise SystemExit('class map length differs from source')
    profile, private_examples = {}, {}
    for policy in (PRIMARY, CONTROL):
        for budget in (256, 1024, 4096):
            for name in CORPORA:
                found = best(policy, name, 16, budget)
                arm = found[2]
                root, entries = dictionary(run, policy, name, 16, budget, arm)
                docs = files[name]
                one_file = {e for e in entries if len(e) > 1 and V.support(e, docs) == 1}
                saved, used, crossing, one_saved = attribution(docs, classes[name], root, one_file)
                total = sum(saved.values())
                multi = [e for e in entries if len(e) > 1]
                row = {'arm': arm, 'emissions': found[0], 'entries': len(entries), 'multi_byte_entries': len(multi),
                       'one_file_entries': len(one_file), 'one_file_saved': one_saved, 'saved_by_kind': dict(saved), 'saved_total': total,
                       'crossing_share': saved['crosses a boundary'] / total if total else 0,
                       'one_file_share': one_saved / total if total else 0,
                       'multibyte_entries_never_used': sum(1 for e in multi if e not in used)}
                if name == 'both':
                    counts, gains = Counter(), Counter()
                    for entry in multi:
                        if entry not in used:
                            continue
                        who = used[entry][1]
                        side = 'both' if any(i < 400 for i in who) and any(i >= 400 for i in who) else 'python_only' if any(i < 400 for i in who) else 'javascript_only'
                        counts[side] += 1
                        gains[side] += used[entry][0]
                    row['entries_used_by'] = {k: counts[k] for k in ('both', 'python_only', 'javascript_only')}
                    row['saved_by_user'] = {k: gains[k] for k in ('both', 'python_only', 'javascript_only')}
                profile[f'{policy}/{name}-K{budget}'] = row
                top = sorted(((used[e][0], len(used[e][1]), e.decode('latin1')) for e in multi if e in used), reverse=True)[:40]
                private_examples[f'{policy}/{name}-K{budget}'] = {
                    'top_entries': top, 'top_crossing': [(gain, piece.decode('latin1')) for piece, gain in crossing.most_common(40)]}
    (out / 'private-examples.json').write_text(json.dumps(private_examples, indent=1))

    endpoints = {'E1': [], 'E2': []}
    for cap in (None, 2048, 4096):
        a, b = best_value(PRIMARY, 'both', 16, 256, cap), best_value(CONTROL, 'both', 16, 256, cap)
        endpoints['E1'].append({'B': cap, 'primary': a, 'control': b, 'reduction': None if a is None or b is None else 1 - a / b})
    for cap in (None, 16384, 32768, 65536):
        endpoints['E2'].append({'B': cap, 'primary': coverage(PRIMARY, 4096, cap), 'control': coverage(CONTROL, 4096, cap), 'files': 800})
    e1, e2 = endpoints['E1'][0], endpoints['E2'][0]
    a64, b64 = best(PRIMARY, 'both', 64, 4096), best(CONTROL, 'both', 64, 4096)
    best64 = cell(PRIMARY, 'both', 64, 4096)[a64[2]]
    share = {row['K']: row for row in sharing if row['policy'] == PRIMARY and row['L'] == 16 and row['B'] is None}
    feasible = [k for k in V.GRID_K if k <= 1024 and share[k]['shared'] is not None]
    predictions = {
        'R1': {'text': 'E1 uncapped: primary at or below control, by less than 2%', 'primary': e1['primary'], 'control': e1['control'],
               'reduction': e1['reduction'], 'held': e1['primary'] <= e1['control'] and e1['reduction'] < 0.02},
        'R2': {'text': 'E2 uncapped: primary spells more files than control and at least 500', 'primary': e2['primary'], 'control': e2['control'],
               'held': e2['primary'] > e2['control'] and e2['primary'] >= 500},
        'R3': {'text': 'K=4096, L=64, both: primary at least 5% below control', 'primary': a64[0], 'control': b64[0],
               'reduction': 1 - a64[0] / b64[0], 'held': a64[0] <= 0.95 * b64[0]},
        'R4': {'text': 'Primary: shared beats separate at every K up to 1024, L=16, uncapped',
               'cells': {k: [share[k]['shared'], share[k]['separate']] for k in feasible},
               'held': all(share[k]['separate'] is None or share[k]['shared'] < share[k]['separate'] for k in feasible)},
        'R5': {'text': 'K=4096, L=64, both: best primary dictionary has a whole-file entry', 'arm': a64[2],
               'whole_file_entries': best64['whole_file_entries'], 'held': best64['whole_file_entries'] >= 1},
    }
    grid = []
    for policy in (PRIMARY, CONTROL):
        for corpus in CORPORA:
            for limit in (2, 4, 8, 16, 32, 64):
                for budget in V.GRID_K:
                    if budget < 128:
                        continue
                    here = cell(policy, corpus, limit, budget)
                    base = [here[a]['emissions'] for a in BASELINES if here[a]['emissions'] is not None]
                    base += [here['bpe'].get('ordinary_emissions')] if here['bpe'].get('ordinary_emissions') else []
                    found = best_value(policy, corpus, limit, budget)
                    if base and found:
                        grid.append({'policy': policy, 'corpus': corpus, 'L': limit, 'K': budget, 'best': found, 'best_baseline': min(base),
                                     'reduction': 1 - found / min(base)})
    summary = {'schema': 'gamma.fixed-source-summary.v2', 'run': verified['run'], 'impl': verified['impl'], 'manifest': verified['manifest'],
               'chains': verified['chains'], 'cells': verified['cells'], 'polished_dictionaries': verified['polished_dictionaries'],
               'stopped_chains': verified['stopped_chains'], 'chain_meta': meta, 'regression': regression, 'census': census,
               'collapse': collapse, 'reachability': reach, 'endpoints': endpoints, 'predictions': predictions, 'sharing': sharing,
               'profile': profile, 'grid': grid, 'table': table}
    (out / 'summary.json').write_text(json.dumps(summary, separators=(',', ':')) + '\n')
    for key, value in predictions.items():
        print(key, 'HELD' if value['held'] else 'FAILED', {k: v for k, v in value.items() if k not in ('text', 'held', 'cells')})
    print(json.dumps(endpoints))


if __name__ == '__main__':
    main()
