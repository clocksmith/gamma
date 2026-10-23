"""Role-slot codec for roles-v1 (FREEZE.md): exact parse, charged declarations, packets, independent decoding.

A slot is (role, ordinal), written as one private-use character PLACE(role, ordinal); no source contains one.
A slot is active when its single-character code is in the dictionary (in mode B, only while END is too). Every
occurrence of a name whose slot is active becomes that character, so literal entries may contain slots. Names whose
slot is inactive stay as spelled text.

Mode B (bind): the body is the abstracted text; right after the body code holding a slot's first occurrence come the
name's own literal codes, then END. Decoding substitutes the declared names, so the output is the source byte for byte.
Mode N (rename-only control): the same body with no declarations; each slot decodes to the canonical identifier
CANON(role, ordinal), so the output is a renamed program, which the execution tests must pass.

Every code (literal, slot, name, END) is one w-bit selection.
"""
import hashlib, json, struct, subprocess
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROLES = ('input', 'output', 'index', 'queue', 'accumulator', 'other')
LETTER = dict(zip(ROLES, 'aripsv'))
END = '\x01END'
BASE = 0xE000
sha = lambda b: hashlib.sha256(b).hexdigest()
_env = {}  # joint module, originals, mode, records


def PLACE(role, ordinal):
    assert 0 <= ordinal < 64
    return chr(BASE + 64 * ROLES.index(role) + ordinal)


def is_slot(s):
    return len(s) == 1 and BASE <= ord(s) < BASE + 64 * len(ROLES)


def slot_of(ch):
    k = ord(ch) - BASE
    return ROLES[k // 64], k % 64


def CANON(ch):
    role, k = slot_of(ch)
    return f'$${LETTER[role]}{k}'


def classify(texts):
    """{key: record} from roles.mjs for texts {key: (text, interface)}. BMP-only is asserted (JS and Python offsets agree)."""
    for t, _ in texts.values():
        assert all(ord(ch) < 0x10000 for ch in t), 'non-BMP character'
        assert not any(BASE <= ord(ch) < BASE + 64 * len(ROLES) for ch in t) and '\x01' not in t and '$$' not in t
    payload = {k: {'text': t, 'interface': i} for k, (t, i) in texts.items()}
    raw = subprocess.run(['/usr/bin/node', str(HERE / 'roles.mjs')], input=json.dumps(payload).encode(), capture_output=True, check=True).stdout
    rows = json.loads(raw)
    for k, r in rows.items():
        for n in r['names']:
            n['slot'] = PLACE(n['role'], n['ordinal'])
            assert all(texts[k][0][s:e] == n['name'] for s, e in n['spans'])
    return rows


def abstract(text, record, active):
    """(abstracted text, {slot: name}) with every active slot's spans replaced by its character."""
    marks, names = [], {}
    for n in record['names']:
        if n['slot'] in active:
            names[n['slot']] = n['name']
            marks.extend((s, e, n['slot']) for s, e in n['spans'])
    out, last = [], 0
    for s, e, ch in sorted(marks):
        assert s >= last
        out.append(text[last:s]); out.append(ch); last = e
    out.append(text[last:])
    return ''.join(out), names


def renamed(text, record, active):
    """Mode N's decoded program: every active slot replaced by its canonical identifier."""
    body, _ = abstract(text, record, active)
    return ''.join(CANON(ch) if is_slot(ch) else ch for ch in body)


def install(joint, mode, records):
    """Route joint.evaluate and joint.prune through this codec (mode 'B' or 'N'); mode 'L' restores the originals."""
    if 'evaluate' not in _env:
        _env['evaluate'], _env['prune'] = joint.evaluate, joint.prune
    _env.update(joint=joint, mode=mode, records=records, cache={})
    joint.evaluate = evaluate if mode in 'BN' else _env['evaluate']
    joint.prune = prune if mode in 'BN' else _env['prune']


def effective(vocab):
    slots = {s for s in vocab if is_slot(s)}
    return slots if _env['mode'] == 'N' or END in vocab else set()


def program(text, eff):
    """(abstracted text, [(slot, name)] in first-occurrence order) for the active slots this program uses."""
    rec = _env['records'][text]
    mine = frozenset(eff & {n['slot'] for n in rec['names']})
    key = (text, mine)
    if key not in _env['cache']:
        body, names = abstract(text, rec, mine)
        order = list(dict.fromkeys(ch for ch in body if is_slot(ch)))
        _env['cache'][key] = (body, [(ch, names[ch]) for ch in order])
    return _env['cache'][key]


def stream(body_parts, decls, name_parts):
    """Selection order: each body code, then for every slot first seen inside it, its name codes and END (mode B)."""
    out, seen = [], set()
    for piece in body_parts:
        out.append(piece)
        if _env['mode'] == 'B':
            for ch in piece:
                if is_slot(ch) and ch not in seen:
                    seen.add(ch); out.extend(name_parts[ch]); out.append(END)
    assert _env['mode'] == 'N' or seen == {ch for ch, _ in decls}
    return tuple(out)


def evaluate(sources, vocab, width, parent=None):
    joint = _env['joint']; base = joint.base
    vocab = joint.order(vocab)
    if len(vocab) > 2 ** width:
        raise ValueError('dictionary exceeds fixed-width budget')
    if _env['mode'] == 'N' and END in vocab:
        raise ValueError('END is not part of mode N')
    eff = effective(vocab)
    peff = effective(parent['vocab']) if parent else None
    lit = [s for s in vocab if s != END]
    tree = base.trie(vocab)
    delta = set(vocab).symmetric_difference(parent['vocab']) if parent else None
    parsed, runs, bodies, chosen = {}, {}, {}, {}
    for pid, variants in sorted(sources.items()):
        options = []
        for variant, text in sorted(variants.items()):
            key = (pid, variant)
            body, decls = program(text, eff)
            if any(s == body or s == text for s in lit):
                raise ValueError('whole-program literal')
            names = [n for _, n in decls] if _env['mode'] == 'B' else []
            reuse = parent is not None and program(text, peff)[0] == body and not any(
                s in body or any(s in n for n in names) for s in delta if s != END and not is_slot(s))
            if reuse:
                parsed[key], runs[key] = parent['parsed'][key], parent['runs'][key]
            else:
                body_parts = tuple(vocab[i] for i in base.segment(body, tree))
                name_parts = {ch: tuple(vocab[i] for i in base.segment(n, tree)) for ch, n in decls} if _env['mode'] == 'B' else {}
                parsed[key] = stream(body_parts, decls, name_parts)
                runs[key] = [body_parts] + [name_parts[ch] for ch, _ in decls if ch in name_parts]
            bodies[key] = body
            options.append((len(parsed[key]), len(text.encode()), variant))
        chosen[pid] = min(options)[2]
    counts = [len(parsed[(pid, v)]) for pid, v in chosen.items()]
    dictionary = len(base.dictionary_bytes(vocab))
    packets = sum(41 + (width * n + 7) // 8 for n in counts)
    return {'vocab': vocab, 'parsed': parsed, 'runs': runs, 'bodies': bodies, 'chosen': chosen, 'selections': sum(counts),
            'package_bytes': dictionary + packets, 'dictionary_bytes': dictionary, 'packet_bytes': packets}


def prune(sources, state, width):
    """Remove unused literal entries. Slot codes and END are never pruned as unused (a slot's character can be needed
    only inside longer entries); the local search may still delete them."""
    base = _env['joint'].base
    used = {s for pid, v in state['chosen'].items() for s in state['parsed'][(pid, v)]}
    removed = sorted(s for s in set(state['vocab']) - used - set(base.ALPHABET) if s != END and not is_slot(s))
    if not removed:
        return state, []
    result = evaluate(sources, set(state['vocab']) - set(removed), width, state)
    assert result['selections'] == state['selections']
    return result, removed


def slot_ranking(sources):
    """Slots used by at least two fitted problems, by total occurrences (then support, then code point)."""
    occ, support = Counter(), defaultdict(set)
    for pid, variants in sources.items():
        for text in variants.values():
            for n in _env['records'][text]['names']:
                occ[n['slot']] += len(n['spans']); support[n['slot']].add(pid)
    return sorted((s for s in occ if len(support[s]) >= 2), key=lambda s: (-occ[s], -len(support[s]), s))


def proposer(sources, absent_slots=16):
    """Absent END (mode B) and the top absent slots first, then chosen-source spans mined from text-contiguous runs."""
    ranking = slot_ranking(sources)
    def propose(srcs, state, limit, fraction=None):
        present = set(state['vocab'])
        head = [END] if _env['mode'] == 'B' and END not in present else []
        head += [s for s in ranking if s not in present][:absent_slots]
        full = set(state['bodies'].values()) | {t for vs in srcs.values() for t in vs.values()}
        scores, owners = defaultdict(dict), defaultdict(set)
        for pid, variant in state['chosen'].items():
            counts = Counter()
            for run in state['runs'][(pid, variant)]:
                for start in range(len(run)):
                    for length in range(2, 7):
                        if start + length > len(run): break
                        fragment = ''.join(run[start:start + length])
                        if len(fragment.encode()) <= 160 and fragment not in full and fragment not in present:
                            counts[fragment] += length - 1
            for fragment, score in counts.items():
                scores[fragment][pid] = max(score, scores[fragment].get(pid, 0)); owners[fragment].add(pid)
        mined = sorted((s for s in scores if len(owners[s]) >= 2), key=lambda s: (-sum(scores[s].values()), len(s.encode()), s))
        return (head + mined)[:limit]
    return propose


def categorize(codes):
    """Action counts for one program's code stream. In mode B the codes after a slot's first use spell its name
    (declaration) and END binds it. The solver's stream has no navigation or corrections; Finish is one submission."""
    c, pending, seen = Counter(), 0, set()
    for s in codes:
        if pending:
            if s == END: c['binding'] += 1; pending -= 1
            else: c['declaration'] += 1
            continue
        if any(is_slot(ch) for ch in s):
            c['reference'] += 1
        else:
            c['literal'] += 1
        if _env['mode'] == 'B':
            fresh = [ch for ch in dict.fromkeys(s) if is_slot(ch) and ch not in seen]
            seen.update(fresh); pending = len(fresh)
    assert not pending
    return {'literal': c['literal'], 'reference': c['reference'], 'declaration': c['declaration'], 'binding': c['binding'],
            'navigation': 0, 'correction': 0, 'submission': 1}


def packet(vocab, codes, width, dictionary):
    ids = {s: i for i, s in enumerate(vocab)}
    payload, value, occupied = bytearray(), 0, 0
    for s in codes:
        value = (value << width) | ids[s]; occupied += width
        while occupied >= 8:
            occupied -= 8; payload.append((value >> occupied) & 255); value &= (1 << occupied) - 1
    if occupied: payload.append(value << (8 - occupied))
    magic = b'LTB1' if _env['mode'] == 'B' else b'LTN1'
    return magic + bytes([width]) + hashlib.sha256(dictionary).digest() + struct.pack('>I', len(codes)) + bytes(payload)


def save_and_verify(folder, sources, state, width):
    """Write the dictionary and packets, decode every packet with decoder.mjs (which writes decoded/<id>.js), and check
    each decoded hash: the source itself in mode B, the canonical renaming in mode N."""
    base = _env['joint'].base
    folder.mkdir(parents=True)
    vocab = state['vocab']; raw = base.dictionary_bytes(vocab)
    (folder / 'dictionary.bin').write_bytes(raw)
    eff = effective(vocab)
    expect, rows = {}, []
    for pid, v in sorted(state['chosen'].items()):
        codes = state['parsed'][(pid, v)]; text = sources[pid][v]
        pk = packet(vocab, codes, width, raw); (folder / f'{pid}.ltr').write_bytes(pk)
        rec = _env['records'][text]
        mine = eff & {n['slot'] for n in rec['names']}
        target = text if _env['mode'] == 'B' else renamed(text, rec, mine)
        expect[str(pid)] = sha(target.encode())
        rows.append({'id': pid, 'selections': len(codes), 'packet_bytes': len(pk), 'packet_sha256': sha(pk),
                     'decoded_sha256': expect[str(pid)], 'source_sha256': sha(text.encode()), 'bound_names': len(mine),
                     'actions': categorize(codes)})
    out = subprocess.run(['/usr/bin/node', str(HERE / 'decoder.mjs'), str(folder)], capture_output=True, check=True, text=True).stdout
    decoded = json.loads(out)
    bad = [k for k, h in expect.items() if decoded.get(k) != h]
    assert not bad, f'decode mismatch: {bad[:5]}'
    m = {'dictionary_sha256': sha(raw), 'dictionary_bytes': len(raw), 'width': width, 'mode': _env['mode'], 'programs': rows,
         'verified': len(expect)}
    (folder / 'manifest.json').write_text(json.dumps(m, indent=1) + '\n')
    return m
