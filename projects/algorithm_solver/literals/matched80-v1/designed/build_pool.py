"""Build the DRAFT designed candidate pool for the matched 80-problem experiment.

Pieces are hand-specified readable units with contract cards. Witnesses are computed
from the pinned scale-v2 sources: a piece is eligible for its style only when its exact
bytes occur in at least two distinct problems of that style. Ineligible pieces stay in
the output as exclusions with their witness counts. Nothing here executes source.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = HERE.parent.parent / 'scale-v2/generated'
MIN_WITNESSES = 2

# Contract templates by kind; per-piece fields override them.
TEMPLATES = {
    'layout': dict(type='source layout', mutation='none', aliasing='none', ordering='n/a', numeric='n/a', complexity='none (no runtime effect)'),
    'delimiter': dict(type='block syntax', mutation='none', aliasing='none', ordering='closes or switches the enclosing block', numeric='n/a', complexity='none'),
    'header': dict(type='function declaration', mutation='declares a function binding in the enclosing scope', aliasing='parameters bind caller references; arrays and objects are shared, not copied', ordering='n/a', numeric='n/a', complexity='O(1) to declare'),
    'scalar-init': dict(type='number', mutation='declares a new local binding', aliasing='none (primitive)', ordering='n/a', numeric='IEEE-754 double; exact for safe integers', complexity='O(1)'),
    'scalar-update': dict(type='number', mutation='reassigns an existing local binding', aliasing='none (primitive)', ordering='n/a', numeric='IEEE-754 double; exact while the result stays a safe integer', complexity='O(1)'),
    'collection-init': dict(mutation='declares a new local binding to a fresh object', aliasing='fresh value; not shared until assigned elsewhere', ordering='n/a', numeric='n/a', complexity='O(1)'),
    'loop': dict(type='loop header', mutation='declares or updates the loop binding', aliasing='iterates the referenced collection without copying it', complexity='O(iterations); body cost not included'),
    'guard': dict(type='conditional header', mutation='none', aliasing='none', ordering='n/a', complexity='O(1)'),
    'control': dict(type='control transfer', mutation='none', aliasing='none', ordering='leaves or restarts the innermost loop or function', numeric='n/a', complexity='O(1)'),
    'return': dict(type='return statement', mutation='none', aliasing='returns the referenced value itself, not a copy', ordering='n/a', complexity='O(1)'),
    'opener': dict(mutation='see callee', aliasing='see callee', ordering='n/a', complexity='see callee'),
}

def piece(style, kind, unit, text, operation, **contract):
    card = dict(TEMPLATES[kind]); card.update(contract)
    return dict(style=style, kind=kind, unit=unit, text=text, operation=operation, contract=card)

C, K = 'canonical', 'compact'
PIECES = [
    # Layout and block syntax (canonical indentation is two spaces per level).
    *[piece(C, 'layout', 'layout', ' ' * n, f'indent {n // 2} level(s)') for n in (2, 4, 6, 8)],
    piece(C, 'delimiter', 'delimiter', '}\n', 'close block'),
    piece(C, 'delimiter', 'delimiter', '} else {\n', 'else branch'),
    piece(C, 'delimiter', 'delimiter', '} else if (', 'else-if branch opener', ordering='tests its condition only when earlier branches failed'),
    # Function frames.
    piece(C, 'header', 'header', 'function solve(values) {\n', 'one-argument entrypoint'),
    piece(C, 'header', 'header', 'function solve(values, other) {\n', 'two-argument entrypoint'),
    piece(C, 'header', 'header', 'function solve(values, other, target) {\n', 'three-argument entrypoint'),
    piece(C, 'header', 'header', 'function helper(values2) {\n', 'one-argument helper'),
    piece(C, 'header', 'header', 'function helper2(values3) {\n', 'second one-argument helper'),
    piece(C, 'header', 'header', 'function helper(values2, other, target) {\n', 'three-argument helper'),
    # Loops.
    piece(C, 'loop', 'complete-header', 'for (const value of values) {\n', 'iterate array values', ordering='index order 0..length-1', numeric='n/a',
          mutation='binds a fresh const per iteration; appending to values during the loop extends iteration'),
    piece(C, 'loop', 'complete-header', 'for (const value2 of values) {\n', 'iterate array values (second binding)', ordering='index order 0..length-1', numeric='n/a'),
    piece(C, 'loop', 'complete-header', 'for (const value3 of values) {\n', 'iterate array values (third binding)', ordering='index order 0..length-1', numeric='n/a'),
    piece(C, 'loop', 'complete-header', 'for (const value3 of values2) {\n', 'iterate helper array values', ordering='index order 0..length-1', numeric='n/a'),
    piece(C, 'loop', 'complete-header', 'for (let index = 0; index < values.length; index += 1) {\n', 'ascending index loop',
          ordering='ascending from 0', numeric='integer index; bound re-read each iteration', mutation='declares index; length changes in the body change the bound'),
    piece(C, 'loop', 'complete-header', 'for (let index = 1; index < values.length; index += 1) {\n', 'ascending index loop from 1',
          ordering='ascending from 1', numeric='integer index; bound re-read each iteration'),
    piece(C, 'loop', 'complete-header', 'for (let index2 = 0; index2 < values.length; index2 += 1) {\n', 'second ascending index loop',
          ordering='ascending from 0', numeric='integer index; bound re-read each iteration'),
    piece(C, 'loop', 'complete-header', 'for (let index = 0; index < count; index += 1) {\n', 'count-bounded index loop',
          ordering='ascending from 0', numeric='integer index; count read each iteration'),
    piece(C, 'loop', 'complete-header', 'while (index < index2) {\n', 'two-pointer loop (strict)', ordering='until pointers meet', numeric='integer comparison'),
    piece(C, 'loop', 'complete-header', 'while (index <= index2) {\n', 'two-pointer or binary-search loop (inclusive)', ordering='until pointers cross', numeric='integer comparison'),
    piece(C, 'loop', 'complete-header', 'while (index + 1 < index2) {\n', 'open-interval binary-search loop', ordering='until the interval has no interior', numeric='integer comparison'),
    piece(C, 'control', 'complete-statement', 'break;\n', 'leave loop'),
    piece(C, 'control', 'complete-statement', 'continue;\n', 'next iteration'),
    # Counters and accumulators.
    *[piece(C, 'scalar-init', 'complete-statement', f'let {name} = 0;\n', f'zero {name}') for name in ('count', 'total', 'index', 'index2', 'maximum', 'value', 'size', 'left')],
    piece(C, 'scalar-init', 'complete-statement', 'let index2 = values.length - 1;\n', 'last index', numeric='-1 for an empty array'),
    piece(C, 'scalar-init', 'complete-statement', 'const count = values.length;\n', 'snapshot length', mutation='declares a const; later length changes are not reflected'),
    *[piece(C, 'scalar-update', 'complete-statement', f'{name} += 1;\n', f'increment {name}') for name in ('count', 'index', 'index2', 'index3', 'size')],
    piece(C, 'scalar-update', 'complete-statement', 'index2 -= 1;\n', 'decrement index2'),
    *[piece(C, 'scalar-update', 'complete-statement', s, op) for s, op in (('index++;\n', 'post-increment index'), ('index2++;\n', 'post-increment index2'), ('index2--;\n', 'post-decrement index2'), ('size++;\n', 'post-increment size'))],
    piece(C, 'scalar-update', 'complete-statement', 'total += value2;\n', 'accumulate a sum', numeric='floating-point addition; string operands concatenate'),
    piece(C, 'scalar-update', 'complete-statement', 'maximum = Math.max(maximum, value);\n', 'running maximum', numeric='Math.max: NaN if either operand is NaN; -0 < +0'),
    piece(C, 'scalar-update', 'complete-statement', 'count = Math.min(count, items.length);\n', 'running minimum against a length', numeric='Math.min: NaN propagates'),
    # Collections: arrays, object maps, counting, stack, copy, binary-search midpoint.
    *[piece(C, 'collection-init', 'complete-statement', f'const {name} = [];\n', f'empty array {name}', type='Array') for name in ('result', 'items', 'items2', 'result2')],
    piece(C, 'collection-init', 'complete-statement', 'const value = {};\n', 'empty object map', type='plain object used as a map',
          ordering='integer-like keys enumerate ascending, then string keys in insertion order', numeric='keys are strings'),
    piece(C, 'collection-init', 'complete-statement', 'const counts = {};\n', 'empty count map', type='plain object used as a count map',
          ordering='integer-like keys enumerate ascending, then string keys in insertion order', numeric='keys are strings'),
    piece(C, 'scalar-update', 'complete-statement', 'counts[value] = (counts[value] || 0) + 1;\n', 'count one occurrence', type='object count map entry',
          mutation='mutates the counts object in place', aliasing='every reference to counts observes the update',
          numeric='key coerced to string; missing or 0 entry treated as 0; safe-integer counts', ordering='new keys follow object key order'),
    piece(C, 'scalar-update', 'complete-statement', 'items[value] = true;\n', 'mark membership', type='object used as a set',
          mutation='mutates items in place', aliasing='shared references observe the mark', numeric='key coerced to string'),
    piece(C, 'scalar-update', 'complete-statement', 'items.pop();\n', 'pop stack top', type='Array used as a stack',
          mutation='removes the last element in place', aliasing='shared references observe the removal', ordering='last in, first out', numeric='n/a', complexity='O(1) amortized'),
    piece(C, 'collection-init', 'complete-statement', 'const items2 = values3.slice();\n', 'shallow array copy', type='Array',
          aliasing='new array; elements are shared references', complexity='O(n)'),
    piece(C, 'scalar-init', 'complete-statement', 'const value3 = value + Math.floor((value2 - value) / 2);\n', 'binary-search midpoint',
          numeric='floors toward negative infinity; avoids (a+b) overflow concerns only within safe integers'),
    # Guards.
    piece(C, 'guard', 'complete-header', 'if (values.length === 0) {\n', 'empty-input guard', numeric='strict equality on length'),
    piece(C, 'guard', 'complete-header', 'if (values.length !== other.length) {\n', 'length-mismatch guard', numeric='strict inequality on lengths'),
    piece(C, 'guard', 'complete-header', 'if (other.length === 0) {\n', 'empty second input guard', numeric='strict equality on length'),
    # Returns.
    *[piece(C, 'return', 'complete-statement', f'return {v};\n', f'return {v}', numeric='n/a' if v in ('result', 'false', 'true') else 'number')
      for v in ('result', 'false', 'true', 'count', 'value', '0', '-1', 'maximum', 'size', 'index')],
    piece(C, 'return', 'complete-statement', "return items.join('');\n", 'return concatenated string', aliasing='returns a new string', complexity='O(total length)', numeric='n/a'),
    # Operation openers (partial units: readable, but not complete statements).
    *[piece(C, 'opener', 'operation-opener', s, op, type=t, numeric=n) for s, op, t, n in (
        ('Math.max(', 'maximum of arguments', 'number function', 'NaN propagates'),
        ('Math.min(', 'minimum of arguments', 'number function', 'NaN propagates'),
        ('Math.floor(', 'floor', 'number function', 'toward negative infinity'),
        ('Math.abs(', 'absolute value', 'number function', '-0 becomes 0'),
        ('.push(', 'append to array', 'Array method; mutates in place; returns new length', 'n/a'),
        ('.length', 'length property', 'Array or string property', 'integer'),
        ("join('')", 'concatenate without separator', 'Array method; returns new string', 'n/a'),
        ('.slice(', 'copy a range', 'Array or string method; returns new value; shallow', 'negative indices count from end'),
        ('new Array(', 'array of length', 'Array constructor', 'single integer argument sets length; holes until filled'),
        ('.fill(0)', 'fill with zero', 'Array method; mutates in place', 'fills existing length only'),
        ('Array.from(', 'array from iterable or length', 'Array factory; returns new array', 'n/a'),
        ('.charCodeAt(', 'UTF-16 code unit', 'string method', 'returns NaN out of range'))],
    # Requested operation families with readable spellings; kept only if witnessed.
    piece(C, 'collection-init', 'complete-statement', 'const queue = [];\n', 'empty queue', type='Array used as a queue'),
    piece(C, 'opener', 'operation-opener', '.shift()', 'dequeue front', type='Array method; O(n) removal of first element'),
    piece(C, 'collection-init', 'complete-statement', 'const seen = new Set();\n', 'empty set', type='Set'),
    piece(C, 'collection-init', 'complete-statement', 'const counts = new Map();\n', 'empty count map', type='Map'),
    piece(C, 'scalar-update', 'complete-statement', 'counts.set(value, (counts.get(value) || 0) + 1);\n', 'count one occurrence (Map)', type='Map count entry'),
    piece(C, 'collection-init', 'complete-statement', 'const adjacency = Array.from({ length: count }, () => []);\n', 'adjacency lists', type='Array of arrays'),
    # Compact style: identifier-free units only, since compact names are per-problem.
    *[piece(K, 'header', 'header', f'function solve({p}){{', f'entrypoint ({p})') for p in ('a', 'a,b', 'b', 'b,c', 'c', 'c,d')],
    piece(K, 'delimiter', 'delimiter', '}else{', 'else branch'),
    piece(K, 'delimiter', 'delimiter', '){', 'close condition, open block'),
    *[piece(K, 'guard' if s in ('if(', 'while(') else 'loop', 'operation-opener', s, op, type='keyword opener', numeric='n/a', ordering='n/a')
      for s, op in (('if(', 'conditional'), ('while(', 'while loop'), ('for(const ', 'for-of loop'), ('for(let ', 'counted loop'))],
    *[piece(K, 'opener', 'operator', s, op, type='operator', numeric=n) for s, op, n in (
        ('===', 'strict equality', 'no coercion; NaN !== NaN'), ('!==', 'strict inequality', 'no coercion'), (' of ', 'for-of separator', 'n/a'))],
    *[piece(K, 'scalar-update' if s != '=0;' else 'scalar-init', 'statement-tail', s, op) for s, op in (('=0;', 'assign zero'), ('+=1;', 'increment'), ('-=1;', 'decrement'))],
    *[piece(K, 'collection-init', 'statement-tail', s, op, type=t) for s, op, t in (('=[];', 'assign empty array', 'Array'), ('={};', 'assign empty object map', 'plain object'))],
    *[piece(K, 'return', 'complete-statement', s, op, numeric='n/a') for s, op in (('return false;', 'return false'), ('return true;', 'return true'), ('return 0;', 'return zero'))],
    piece(K, 'return', 'operation-opener', 'return ', 'return opener', numeric='n/a'),
    *[piece(K, 'control', 'complete-statement', s, op) for s, op in (('break;', 'leave loop'), ('continue;', 'next iteration'))],
    *[piece(K, 'opener', 'operation-opener', s, op, type=t, numeric=n) for s, op, t, n in (
        ('Math.max(', 'maximum of arguments', 'number function', 'NaN propagates'), ('Math.min(', 'minimum of arguments', 'number function', 'NaN propagates'),
        ('Math.floor(', 'floor', 'number function', 'toward negative infinity'), ('Math.abs(', 'absolute value', 'number function', '-0 becomes 0'),
        ('.push(', 'append to array', 'Array method; mutates in place', 'n/a'), ('.length', 'length property', 'property', 'integer'),
        ('.pop(', 'pop stack top', 'Array method; mutates in place', 'n/a'), ('.join(', 'join elements', 'Array method; new string', 'n/a'),
        ('.slice(', 'copy a range', 'shallow copy', 'negative indices count from end'), ('.fill(', 'fill array', 'Array method; mutates in place', 'existing length only'),
        ('new Array(', 'array of length', 'constructor', 'holes until filled'), ('Array.from(', 'array factory', 'factory', 'n/a'),
        ('.charCodeAt(', 'UTF-16 code unit', 'string method', 'NaN out of range'), ('.split(', 'split string', 'string method', 'n/a'),
        ('.shift()', 'dequeue front', 'Array method; O(n)', 'n/a'), ('new Set(', 'set', 'constructor', 'SameValueZero keys'),
        ('new Map(', 'map', 'constructor', 'SameValueZero keys'))],
]

def main():
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    manifest_bytes = (SOURCES / 'manifest.json').read_bytes()
    rows = json.loads(manifest_bytes)['rows']
    texts = {style: {r['id']: (SOURCES / r['file']).read_text() for r in rows if r['variant'] == style} for style in (C, K)}
    pool, excluded = [], []
    for i, item in enumerate(PIECES):
        # Single characters already exist in the charged 96-entry fallback alphabet.
        if len(item['text']) < 2: raise SystemExit(f"single-character piece duplicates the fallback: {item['text']!r}")
        witnesses = sorted(pid for pid, src in texts[item['style']].items() if item['text'] in src)
        entry = dict(id=f"d{i:03d}", **item, witnesses=witnesses, witness_count=len(witnesses))
        (pool if len(witnesses) >= MIN_WITNESSES else excluded).append(entry)
    seen = {}
    for entry in pool:
        key = (entry['style'], entry['text'])
        if key in seen: raise SystemExit(f"duplicate piece {key!r}")
        seen[key] = entry['id']
    out = dict(schema='gamma.matched80.designed-pool.v1', status='Owner-approved 2026-10-21; frozen with ../contract.json before any arm ran',
               sources_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(), min_witnesses=MIN_WITNESSES,
               builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               counts={style: sum(e['style'] == style for e in pool) for style in (C, K)},
               excluded_counts={style: sum(e['style'] == style for e in excluded) for style in (C, K)},
               pool=pool, excluded=excluded)
    if a.output.exists(): raise SystemExit(f'refusing to overwrite {a.output}')
    a.output.write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out['counts']), 'excluded', json.dumps(out['excluded_counts']))
    for e in excluded: print(f"  excluded {e['style']:9s} {e['witness_count']} witness(es): {e['text']!r}")

if __name__ == '__main__':
    main()
