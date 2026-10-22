"""Readable-units-v1: a frozen lexical rule that turns sources into readable candidate units.

A unit is a name, a member name, a keyword head, a statement tail, an operator run or an
indentation run, as defined below. Units only propose candidates; measured exact gain
decides admission. Nothing here executes source.
"""
import re
from collections import defaultdict

PUNCT = ['>>>=', '...', '===', '!==', '>>>', '**=', '<<=', '>>=', '&&=', '||=', '??=', '=>', '==', '!=', '<=', '>=',
         '&&', '||', '??', '?.', '++', '--', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '**', '<<', '>>']
TOKEN = re.compile(r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)|(?P<number>\d+(?:\.\d+)?)"
                   r"|(?P<string>'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"|`(?:[^`\\]|\\.)*`)"
                   r"|(?P<newline>\n)|(?P<space>[ \t])|(?P<punct>" + '|'.join(map(re.escape, PUNCT)) + r"|.)", re.S)
KEYWORDS = {'return', 'const', 'let', 'var', 'if', 'for', 'while', 'else', 'function', 'new', 'of', 'in', 'throw',
            'typeof', 'break', 'continue', 'do', 'switch', 'case', 'default'}
CLASSES = ('name', 'member', 'head', 'tail', 'operator', 'indent')
MAX_BYTES = 32
MAX_HEAD_TOKENS = 3
OPERAND = {'name', 'number', 'string'}


def tokens(text):
    """(kind, text, start) for every token; spaces are single-character tokens."""
    return [(m.lastgroup, m.group(), m.start()) for m in TOKEN.finditer(text)]


def boundaries(text):
    return {start for _, _, start in tokens(text)} | {len(text)}


def units_of(text):
    """Every readable unit occurrence in one source, as (class, unit) pairs."""
    toks = tokens(text)
    found = []
    for i, (kind, value, _) in enumerate(toks):
        if kind != 'name':
            continue
        found.append(('name', value))
        if i and toks[i - 1][1] == '.':
            found.append(('member', '.' + value))
        if value in KEYWORDS:
            run = []
            for k, v, _ in toks[i + 1:i + 1 + MAX_HEAD_TOKENS]:
                if k in OPERAND or k == 'newline':
                    break
                run.append(v)
            if run:
                found.append(('head', value + ''.join(run)))
    # Maximal non-operand runs, split after each newline; leading spaces after a newline are indentation.
    run, runs = [], []
    for kind, value, _ in toks + [('name', '', len(text))]:
        if kind in OPERAND:
            if run:
                runs.append(''.join(run))
            run = []
        else:
            run.append(value)
    for chunk in runs:
        lines = chunk.split('\n')
        for n, line in enumerate(lines):
            piece = line + ('\n' if n < len(lines) - 1 else '')
            if n:
                body = piece.lstrip(' ')
                if len(piece) - len(body) >= 2:
                    found.append(('indent', piece[:len(piece) - len(body)]))
                piece = body
            if len(piece) < 2:
                continue
            found.append(('tail' if '\n' in piece or any(c in piece for c in ';{}') else 'operator', piece))
    return found


def extract(texts, min_witnesses=2):
    """Units witnessed in at least min_witnesses problems, with one class each (first class in CLASSES order)."""
    owners, classes = defaultdict(set), defaultdict(set)
    for key, text in texts.items():
        for cls, unit in units_of(text):
            if len(unit.encode()) <= MAX_BYTES and unit != text:
                owners[unit].add(key)
                classes[unit].add(cls)
    return {unit: min(classes[unit], key=CLASSES.index) for unit in sorted(owners) if len(owners[unit]) >= min_witnesses}


def aligned_fraction(text, parts):
    """Share of selections whose start and end both fall on token boundaries."""
    edges, pos, aligned = boundaries(text), 0, 0
    for part in parts:
        aligned += pos in edges and pos + len(part) in edges
        pos += len(part)
    assert pos == len(text)
    return aligned / len(parts)
