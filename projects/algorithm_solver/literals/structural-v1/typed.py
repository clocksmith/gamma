"""Typed-component codec for structural-v1: exact parse, charged dictionary and packets, independent decoding.

A vocabulary is a set of strings. Literal entries are source text; a component is the code '\\x01<id>' and
END is '\\x01END' (no source contains '\\x01'). With no component in the vocabulary, evaluate() delegates to the
unchanged literal parser, so literal arms are identical to the canonical codec.

Selection stream (preorder): a component code, then one operand per distinct hole in first-use order. An id
operand is exactly one identifier-shaped literal code; every other operand is codes closed by END. Each code is
one w-bit selection. Nesting depth is at most 8.
"""
import hashlib, json, re, struct, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
END = '\x01END'
DEPTH = 8
IDENT = re.compile(r'^[A-Za-z_$][A-Za-z0-9_$]*$')
INF = float('inf')
sha = lambda b: hashlib.sha256(b).hexdigest()
code = lambda cid: '\x01' + cid
is_code = lambda s: s.startswith('\x01')

COMPONENTS = {c['id']: c for c in json.loads((HERE / 'components.json').read_text())['components']}
_parts = {}
_env = {}  # joint module, original evaluate, match tables


def parts(cid):
    if cid not in _parts:
        out, last = [], 0
        t = COMPONENTS[cid]['template']
        for m in re.finditer(r'\$\{([A-Z])\}', t):
            if m.start() > last: out.append(('fixed', t[last:m.start()]))
            out.append(('hole', m.group(1))); last = m.end()
        if last < len(t): out.append(('fixed', t[last:]))
        _parts[cid] = out
    return _parts[cid]


def holes(cid):
    """Distinct holes in first-use order."""
    return list(dict.fromkeys(h for k, h in parts(cid) if k == 'hole'))


def needs_end(cid):
    return any(COMPONENTS[cid]['holes'][h] != 'id' for h in holes(cid))


def find_matches(texts):
    """{text_sha: [match]} from matcher.mjs, for texts {key: text}. Offsets are JS (UTF-16) indices; BMP-only is asserted."""
    for t in texts.values():
        assert all(ord(ch) < 0x10000 for ch in t), 'non-BMP character: JS and Python offsets would differ'
    raw = subprocess.run(['/usr/bin/node', str(HERE / 'matcher.mjs'), str(HERE / 'components.json'), '/dev/stdin'],
                         input=json.dumps(texts).encode(), capture_output=True, check=True).stdout
    rows = json.loads(raw)
    return {k: rows[k] for k in texts}


def install(joint, matches):
    """Route joint.evaluate through the typed parser. matches: {text: [match dicts]}."""
    if 'original' not in _env:
        _env['original'] = joint.evaluate
    _env.update(joint=joint, matches=matches)
    joint.evaluate = evaluate


def order(vocab):
    return _env['joint'].order(vocab)


def dictionary_bytes(vocab):
    """LTD1 list of every code's bytes (component codes as '\\x01<id>'), then LTC1 with the used components' definitions."""
    fields = [b'LTD1', struct.pack('>I', len(vocab))]
    for s in vocab:
        raw = s.encode('utf-8'); fields.extend((struct.pack('>I', len(raw)), raw))
    used = sorted(s[1:] for s in vocab if is_code(s) and s != END)
    if used:
        block = json.dumps([{'id': c, 'template': COMPONENTS[c]['template'], 'holes': COMPONENTS[c]['holes']} for c in used],
                           separators=(',', ':'), ensure_ascii=False).encode()
        fields.extend((b'LTC1', struct.pack('>I', len(block)), block))
    return b''.join(fields)


def free_bytes(m, text):
    """Bytes a match emits beyond its charged operands: fixed text plus repeated-hole copies."""
    span = len(text[m['s']:m['e']].encode())
    return span - sum(len(text[s:e].encode()) for s, e in m['holes'].values())


def admissible(m, text):
    """Whole-solution exclusion: a match whose free bytes are at least half its program is never used."""
    return 2 * free_bytes(m, text) < len(text.encode())


def parse(text, lit_index, tree, litset, comps, has_end, base):
    """Minimum-code typed parse of text. Returns (codes, runs): runs are text-contiguous literal stretches."""
    ms = [m for m in _env['matches'][text] if m['c'] in comps and (has_end or not needs_end(m['c'])) and admissible(m, text)]
    if not ms:
        seq = tuple(lit_index[i] for i in base.segment(text, tree))
        return seq, [seq]
    n = len(text)
    lit_at = [[] for _ in range(n)]
    for i in range(n):
        node, j = tree, i
        while j < n and text[j] in node:
            node = node[text[j]]; j += 1
            if None in node: lit_at[i].append(j)
    comp_at = {}
    for m in ms: comp_at.setdefault(m['s'], []).append(m)
    memo = {}

    def operand_cost(m, h, depth):
        s, e = m['holes'][h]
        if COMPONENTS[m['c']]['holes'][h] == 'id':
            t = text[s:e]
            return (1, ('id', t)) if t in litset and IDENT.match(t) else (INF, None)
        c, _ = span(s, e, depth + 1)
        return c + 1, ('seq', s, e, depth + 1)

    def edge(m, depth):
        if depth >= DEPTH: return INF, None
        total, ops = 1, []
        for h in holes(m['c']):
            c, op = operand_cost(m, h, depth)
            total += c
            if total == INF: return INF, None
            ops.append(op)
        return total, ops

    def span(a, b, depth):
        key = (a, b, depth)
        if key in memo: return memo[key]
        cost = {a: 0}; back = {}
        for i in range(a, b):
            if i not in cost: continue
            ci = cost[i]
            for j in lit_at[i]:
                if j <= b and ci + 1 < cost.get(j, INF): cost[j] = ci + 1; back[j] = ('lit', i)
            for m in comp_at.get(i, ()):
                if m['e'] <= b:  # a match may fill its enclosing hole exactly; edge() enforces the depth limit
                    c, ops = edge(m, depth)
                    if ci + c < cost.get(m['e'], INF): cost[m['e']] = ci + c; back[m['e']] = ('comp', i, m, ops)
        memo[key] = (cost.get(b, INF), back)
        return memo[key]

    def emit(a, b, depth, out, runs):
        _, back = span(a, b, depth)
        steps, j = [], b
        while j > a:
            step = back[j]; steps.append((step, j)); j = step[1]
        steps.reverse()
        run = []
        for step, j in steps:
            if step[0] == 'lit':
                piece = text[step[1]:j]; out.append(piece); run.append(piece)
            else:
                if run: runs.append(tuple(run)); run = []
                _, i, m, ops = step
                out.append(code(m['c']))
                for op in ops:
                    if op[0] == 'id':
                        out.append(op[1]); runs.append((op[1],))
                    else:
                        emit(op[1], op[2], op[3], out, runs); out.append(END)
        if run: runs.append(tuple(run))

    total, _ = span(0, n, 0)
    assert total < INF, 'unrepresentable'
    out, runs = [], []
    emit(0, n, 0, out, runs)
    assert len(out) == total
    return tuple(out), runs


def evaluate(sources, vocab, width, parent=None):
    joint, base = _env['joint'], _env['joint'].base
    if not any(is_code(s) for s in vocab):
        return _env['original'](sources, vocab, width, parent)
    vocab = order(vocab)
    if len(vocab) > 2 ** width:
        raise ValueError('dictionary exceeds fixed-width budget')
    lit = [s for s in vocab if not is_code(s)]
    if any(s == text for variants in sources.values() for text in variants.values() for s in lit):
        raise ValueError('whole-program literal')
    tree, litset = base.trie(lit), set(lit)
    comps = {s[1:] for s in vocab if is_code(s) and s != END}
    has_end = END in vocab
    delta = set(vocab).symmetric_difference(parent['vocab']) if parent and 'runs' in parent else None
    parsed, runs, chosen = {}, {}, {}
    for pid, variants in sorted(sources.items()):
        options = []
        for variant, text in sorted(variants.items()):
            key = (pid, variant)
            touched = delta is None or any(
                (s == END and _env['matches'][text]) or (is_code(s) and s != END and any(m['c'] == s[1:] for m in _env['matches'][text]))
                or (not is_code(s) and s in text) for s in delta)
            if not touched:
                parsed[key], runs[key] = parent['parsed'][key], parent['runs'][key]
            else:
                parsed[key], runs[key] = parse(text, lit, tree, litset, comps, has_end, base)
            options.append((len(parsed[key]), len(text.encode()), variant))
        chosen[pid] = min(options)[2]
    counts = [len(parsed[(pid, v)]) for pid, v in chosen.items()]
    dictionary = len(dictionary_bytes(vocab))
    packets = sum(41 + (width * n + 7) // 8 for n in counts)
    return {'vocab': vocab, 'parsed': parsed, 'runs': runs, 'chosen': chosen, 'selections': sum(counts),
            'package_bytes': dictionary + packets, 'dictionary_bytes': dictionary, 'packet_bytes': packets}


def proposals(sources, state, limit, allowed=()):
    """Chosen-source span proposals over text-contiguous literal runs only; absent allowed components first."""
    from collections import Counter, defaultdict
    present = set(state['vocab'])
    absent = [code(c) for c in sorted(allowed) if code(c) not in present]
    if allowed and END not in present:
        absent.append(END)
    scores, owners = defaultdict(dict), defaultdict(set)
    full = {t for vs in sources.values() for t in vs.values()}
    for pid, variant in state['chosen'].items():
        stretches = state['runs'][(pid, variant)] if 'runs' in state else [state['parsed'][(pid, variant)]]
        counts = Counter()
        for run in stretches:
            for start in range(len(run)):
                for length in range(2, 7):
                    if start + length > len(run): break
                    fragment = ''.join(run[start:start + length])
                    if len(fragment.encode()) <= 160 and fragment not in full and fragment not in present:
                        counts[fragment] += length - 1
        for fragment, score in counts.items():
            scores[fragment][pid] = max(score, scores[fragment].get(pid, 0)); owners[fragment].add(pid)
    mined = sorted((s for s in scores if len(owners[s]) >= 2), key=lambda s: (-sum(scores[s].values()), len(s.encode()), s))
    return (absent + mined)[:limit]


def packet(vocab, codes, width, dictionary):
    ids = {s: i for i, s in enumerate(vocab)}
    payload, value, occupied = bytearray(), 0, 0
    for s in codes:
        value = (value << width) | ids[s]; occupied += width
        while occupied >= 8:
            occupied -= 8; payload.append((value >> occupied) & 255); value &= (1 << occupied) - 1
    if occupied: payload.append(value << (8 - occupied))
    return b'LTT1' + bytes([width]) + hashlib.sha256(dictionary).digest() + struct.pack('>I', len(codes)) + bytes(payload)


def save_and_verify(folder, sources, state, width):
    """Write the dictionary and packets, then decode every packet with decoder.mjs and check each source hash."""
    folder.mkdir(parents=True)
    vocab = state['vocab']; raw = dictionary_bytes(vocab)
    (folder / 'dictionary.bin').write_bytes(raw)
    expect, rows = {}, []
    for pid, v in sorted(state['chosen'].items()):
        codes = state['parsed'][(pid, v)]; text = sources[pid][v]
        pk = packet(vocab, codes, width, raw); (folder / f'{pid}.ltt').write_bytes(pk)
        expect[str(pid)] = sha(text.encode())
        rows.append({'id': pid, 'variant': v, 'selections': len(codes), 'packet_bytes': len(pk), 'packet_sha256': sha(pk),
                     'source_sha256': expect[str(pid)], 'components': sum(is_code(s) and s != END for s in codes),
                     'ends': sum(s == END for s in codes)})
    out = subprocess.run(['/usr/bin/node', str(HERE / 'decoder.mjs'), str(folder)], capture_output=True, check=True, text=True).stdout
    decoded = json.loads(out)
    bad = [k for k, h in expect.items() if decoded.get(k) != h]
    assert not bad, f'decode mismatch: {bad[:5]}'
    m = {'dictionary_sha256': sha(raw), 'dictionary_bytes': len(raw), 'width': width, 'programs': rows, 'verified': len(expect)}
    (folder / 'manifest.json').write_text(json.dumps(m, indent=1) + '\n')
    return m
