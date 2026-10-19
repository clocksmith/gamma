"""Reject provably incompatible public interfaces, without inferring identity.

Only caller-supplied public data and indexed declarations are consulted. Unknown
annotations, opaque node encodings and empty containers remain inconclusive.
Passing this filter is never permission to return an answer.
"""
import ast


def accepts(annotation, value):
    try:
        node = ast.parse(annotation or 'Any', mode='eval').body
    except (SyntaxError, TypeError):
        return True
    return _accepts(node, value)


def _accepts(node, value):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return accepts(node.value, value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _accepts(node.left, value) or _accepts(node.right, value)
    if isinstance(node, ast.Subscript):
        name = node.value.id if isinstance(node.value, ast.Name) else getattr(node.value, 'attr', '')
        if name in ('List', 'list', 'Sequence'):
            return isinstance(value, list) and all(_accepts(node.slice, item) for item in value)
        if name == 'Optional':
            return value is None or _accepts(node.slice, value)
        if name == 'Union' and isinstance(node.slice, ast.Tuple):
            return any(_accepts(item, value) for item in node.slice.elts)
        return True
    name = node.id if isinstance(node, ast.Name) else ''
    if name in ('int', 'bool', 'str'):
        return type(value) is {'int': int, 'bool': bool, 'str': str}[name]
    if name == 'float':
        return type(value) in (int, float)
    if isinstance(node, ast.Constant) and node.value is None:
        return value is None
    return True


def mismatch(entry, examples):
    """Return a concrete incompatibility, or None (compatible OR unknown)."""
    if not entry.entry.get('method') or not entry.params:
        return None
    return_type = None
    try:
        tree = ast.parse(entry.starter_code)
        for cls in tree.body:
            if isinstance(cls, ast.ClassDef) and cls.name == entry.entry.get('class', 'Solution'):
                for fn in cls.body:
                    if isinstance(fn, ast.FunctionDef) and fn.name == entry.entry['method'] and fn.returns:
                        return_type = ast.unparse(fn.returns)
    except SyntaxError:
        pass
    for example in examples:
        # Keyword interfaces may be explicitly renamed by the caller. Leave
        # their binding to the existing execution boundary.
        if example.get('kwargs') or 'args' not in example:
            continue
        args = example['args']
        if len(args) != len(entry.params):
            return 'argument_count'
        for value, (_, annotation) in zip(args, entry.params):
            if not accepts(annotation, value):
                return 'argument_type'
        # In-place tests describe mutated inputs rather than the return value.
        if example.get('compare', 'return') == 'return' and 'expected' in example and return_type:
            if not accepts(return_type, example['expected']):
                return 'return_type'
    return None


def filter_candidates(candidates, lookup, examples):
    kept, rejected = [], []
    for candidate in candidates:
        entry = lookup.entries[lookup.by_key[candidate['key']]]
        reason = mismatch(entry, examples)
        if reason:
            rejected.append({'key': entry.key, 'reason': reason})
        else:
            kept.append(candidate)
    return kept, rejected
