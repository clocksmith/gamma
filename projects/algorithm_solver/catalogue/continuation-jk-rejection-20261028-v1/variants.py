"""Seeded wrong variants of exact J/K sources for judge rejection measurement.

A variant is the byte-preserved original source followed by a fixed wrapper that
replaces the exported solve. Every wrapper decision is a pure function of the
call arguments, the call position in its process and, for aliasing, the
original result. The host mirrors each decision per language, so the cases on
which a variant must be rejected are known before any execution. The variants
are not candidates and confer nothing on the originals.
"""
from __future__ import annotations
import json

LARGE = 1000
SAFE = 2**53-1

# name: (kind, rejection reasons that confirm the intended defect class)
OPERATORS = {
    'control-copy': ('control', ()),
    'wrong-always': ('value', ('result_value',)),
    'wrong-on-degenerate': ('value', ('result_value',)),
    'wrong-on-large': ('value', ('result_value',)),
    'wrong-on-duplicates': ('value', ('result_value',)),
    'wrong-on-negative': ('value', ('result_value',)),
    'wrong-on-zero': ('value', ('result_value',)),
    'wrong-on-repeat-call': ('state', ('result_value',)),
    'wrong-type': ('interface', ('result_type', 'candidate_error')),
    'input-mutation': ('effects', ('input_effects',)),
    'alias-equal-input': ('alias', ('return_aliases',)),
    'slow-on-large': ('resource', ('sandbox_process_failure',)),
    'memory-on-large': ('resource', ('sandbox_process_failure', 'candidate_error')),
}

PYTHON = r'''

# Gamma seeded rejection variant; not a candidate.
def __gamma_seeded_variant(original, op):
    import copy, time
    state = {'calls': 0, 'depth': 0}
    def safe_int(x):
        return type(x) is int and abs(x) <= 9007199254740991
    def ints(args):
        return [x for a in args for x in (a if type(a) is list else [a]) if safe_int(x)]
    def same(a, b):
        if type(a) is not type(b):
            return False
        if type(a) is list:
            return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        if type(a) is dict:
            return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
        return a == b
    def triggered(args, position):
        lengths = [len(a) for a in args if type(a) in (list, str)]
        if op in ('wrong-always', 'wrong-type'):
            return True
        if op == 'wrong-on-degenerate':
            return bool(lengths) and max(lengths) <= 1
        if op in ('wrong-on-large', 'slow-on-large', 'memory-on-large'):
            return bool(lengths) and max(lengths) >= 1000
        if op == 'wrong-on-duplicates':
            for a in args:
                if type(a) is list and len(a) > 1 and (all(safe_int(x) for x in a) or all(type(x) is str for x in a)):
                    if len(set(a)) < len(a):
                        return True
            return False
        if op == 'wrong-on-negative':
            return any(x < 0 for x in ints(args))
        if op == 'wrong-on-zero':
            return any(x == 0 for x in ints(args))
        if op == 'wrong-on-repeat-call':
            return position >= 1
        if op == 'input-mutation':
            return any(type(a) is list for a in args)
        return False
    def perturb(r):
        if type(r) is bool:
            return not r
        if type(r) in (int, float):
            return r + 1
        if type(r) is str:
            return r + 'a'
        if type(r) is list:
            return r[:-1] if r else [0]
        if type(r) is dict:
            return dict(r, __gamma_seeded__=0)
        return 0
    def retype(r):
        if type(r) is bool:
            return int(r)
        if type(r) is int:
            return float(r)
        if type(r) is float:
            return str(r)
        if type(r) is str:
            return [r]
        if type(r) is list:
            return {str(i): x for i, x in enumerate(r)}
        if r is None:
            return ''
        return 0
    def alias(args, r):
        lists = [a for a in args if type(a) is list]
        if type(r) is not list:
            return r
        for a in lists:
            if same(r, a):
                return a
        for a in lists:
            for i, x in enumerate(r):
                if type(x) is list:
                    for y in a:
                        if type(y) is list and same(x, y):
                            r = list(r); r[i] = y
                            return r
        return r
    module = globals()
    def solve(*args):
        if state['depth']:
            return original(*args)
        position = state['calls']; state['calls'] += 1; state['depth'] = 1
        # Recursive or helper calls resolve the global name to the original
        # while it runs, so the wrapper adds no frames below the outer call.
        module['solve'] = original
        try:
            if op == 'control-copy':
                return copy.deepcopy(original(*copy.deepcopy(args)))
            fire = triggered(args, position)
            if fire and op == 'slow-on-large':
                end = time.process_time() + 12
                while time.process_time() < end:
                    pass
            if fire and op == 'memory-on-large':
                hold = [bytearray(64*1024**2) for _ in range(40)]
            result = original(*args)
            if op == 'alias-equal-input':
                return alias(args, result)
            if not fire:
                return result
            if op == 'input-mutation':
                a = next(a for a in args if type(a) is list); a.append(a[-1] if a else 0)
                return result
            if op == 'wrong-type':
                return retype(result)
            if op.startswith('wrong-'):
                return perturb(result)
            return result
        finally:
            state['depth'] = 0
            module['solve'] = solve
    return solve

solve = __gamma_seeded_variant(solve, %OP%)
'''

JAVASCRIPT = r'''
;// Gamma seeded rejection variant; not a candidate.
module.exports = (function (original, op) {
  const state = {calls: 0, depth: 0};
  const safeInt = x => typeof x === 'number' && Number.isInteger(x) && Math.abs(x) <= 9007199254740991;
  const ints = args => { const out = []; for (const a of args) for (const x of (Array.isArray(a) ? a : [a])) if (safeInt(x)) out.push(x); return out; };
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  function triggered(args, position) {
    const lengths = args.filter(a => Array.isArray(a) || typeof a === 'string').map(a => a.length);
    if (op === 'wrong-always' || op === 'wrong-type') return true;
    if (op === 'wrong-on-degenerate') return lengths.length > 0 && Math.max(...lengths) <= 1;
    if (op === 'wrong-on-large' || op === 'slow-on-large' || op === 'memory-on-large') return lengths.length > 0 && Math.max(...lengths) >= 1000;
    if (op === 'wrong-on-duplicates') {
      for (const a of args) if (Array.isArray(a) && a.length > 1 && (a.every(safeInt) || a.every(x => typeof x === 'string')))
        if (new Set(a).size < a.length) return true;
      return false;
    }
    if (op === 'wrong-on-negative') return ints(args).some(x => x < 0);
    if (op === 'wrong-on-zero') return ints(args).some(x => x === 0);
    if (op === 'wrong-on-repeat-call') return position >= 1;
    if (op === 'input-mutation') return args.some(a => Array.isArray(a));
    return false;
  }
  function perturb(r) {
    if (typeof r === 'boolean') return !r;
    if (typeof r === 'number') return r + 1;
    if (typeof r === 'bigint') return r + 1n;
    if (typeof r === 'string') return r + 'a';
    if (Array.isArray(r)) return r.length ? r.slice(0, -1) : [0];
    if (r !== null && typeof r === 'object' && !('val' in r)) return Object.assign({}, r, {__gamma_seeded__: 0});
    return 0;
  }
  function retype(r) {
    if (typeof r === 'boolean') return r ? 1 : 0;
    if (typeof r === 'number') return String(r);
    if (typeof r === 'string') return [r];
    if (Array.isArray(r)) return r.length;
    return 0;
  }
  function alias(args, r) {
    const lists = args.filter(a => Array.isArray(a));
    if (!Array.isArray(r)) return r;
    for (const a of lists) if (same(r, a)) return a;
    for (const a of lists) for (let i = 0; i < r.length; i++) if (Array.isArray(r[i]))
      for (const y of a) if (Array.isArray(y) && same(r[i], y)) { const copy = r.slice(); copy[i] = y; return copy; }
    return r;
  }
  return function solve(...args) {
    if (state.depth) return original(...args);
    const position = state.calls++; state.depth = 1;
    try {
      if (op === 'control-copy') return structuredClone(original(...structuredClone(args)));
      const fire = triggered(args, position);
      if (fire && op === 'slow-on-large') { const end = Date.now() + 12000; while (Date.now() < end) {} }
      if (fire && op === 'memory-on-large') { const hold = []; for (let i = 0; i < 64; i++) hold.push(new Array(4e6).fill(i)); }
      const result = original(...args);
      if (op === 'alias-equal-input') return alias(args, result);
      if (!fire) return result;
      if (op === 'input-mutation') { const a = args.find(x => Array.isArray(x)); a.push(a.length ? a[a.length - 1] : 0); return result; }
      if (op === 'wrong-type') return retype(result);
      if (op.startsWith('wrong-')) return perturb(result);
      return result;
    } finally { state.depth = 0; }
  };
})(module.exports, %OP%);
'''


def variant_source(original: bytes, language: str, op: str) -> bytes:
    if op not in OPERATORS:
        raise ValueError('unknown operator')
    template = PYTHON if language == 'python' else JAVASCRIPT
    return original + template.replace('%OP%', json.dumps(op)).encode()


# Host mirrors of the wrapper decisions, evaluated on wire-format JSON arguments.
# Wire bigint and node encodings are dicts; both runtimes decode them to values
# that the wrappers ignore, so the host ignores them too.

def _js_int(x):
    return type(x) in (int, float) and type(x) is not bool and float(x).is_integer() and abs(x) <= SAFE


def _is_int(x, language):
    if language == 'python':
        return type(x) is int and abs(x) <= SAFE
    return _js_int(x)


def _length(x, language):
    return len(x) if language == 'python' or type(x) is list else len(x.encode('utf-16-le'))//2


def _ints(args, language):
    return [x for a in args for x in (a if type(a) is list else [a]) if _is_int(x, language)]


def _js_value(x):
    if type(x) is list:
        return [_js_value(y) for y in x]
    if type(x) is dict:
        return {k: _js_value(v) for k, v in x.items()}
    return int(x) if type(x) is float and x.is_integer() else x


def _same(a, b, language):
    if language == 'javascript':
        return json.dumps(_js_value(a), separators=(',', ':')) == json.dumps(_js_value(b), separators=(',', ':'))
    if type(a) is not type(b):
        return False
    if type(a) is list:
        return len(a) == len(b) and all(_same(x, y, language) for x, y in zip(a, b))
    if type(a) is dict:
        return set(a) == set(b) and all(_same(a[k], b[k], language) for k in a)
    return a == b


def triggers(op, language, args, position, expected):
    """True when the wrapper changes the observable outcome of this call."""
    lengths = [_length(a, language) for a in args if type(a) in (list, str)]
    if op == 'control-copy':
        return False
    if op in ('wrong-always', 'wrong-type'):
        return True
    if op == 'wrong-on-degenerate':
        return bool(lengths) and max(lengths) <= 1
    if op in ('wrong-on-large', 'slow-on-large', 'memory-on-large'):
        return bool(lengths) and max(lengths) >= LARGE
    if op == 'wrong-on-duplicates':
        for a in args:
            if type(a) is list and len(a) > 1 and (all(_is_int(x, language) for x in a) or all(type(x) is str for x in a)):
                values = [int(x) if type(x) is float else x for x in a]
                if len(set(values)) < len(values):
                    return True
        return False
    if op == 'wrong-on-negative':
        return any(x < 0 for x in _ints(args, language))
    if op == 'wrong-on-zero':
        return any(x == 0 for x in _ints(args, language))
    if op == 'wrong-on-repeat-call':
        return position >= 1
    if op == 'input-mutation':
        return any(type(a) is list for a in args)
    if op == 'alias-equal-input':
        if type(expected) is not list:
            return False
        lists = [a for a in args if type(a) is list]
        if any(_same(expected, a, language) for a in lists):
            return True
        return any(type(x) is list and type(y) is list and _same(x, y, language)
                   for a in lists for x in expected for y in a)
    raise ValueError('unknown operator')
