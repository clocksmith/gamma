"""Conservative Python graph adapter for binding-descent-v1's pure optimizer.

No corpus loader. Parameters and captured/dynamic bindings remain fixed. Names in
comprehensions/lambdas/formatted strings remain reserved globally. Try/TryStar
retains the whole source because caught exception messages expose binding names.
"""
import ast
import keyword
import re
import symtable

REFLECTION = {
    'eval', 'exec', 'compile', 'locals', 'globals', 'vars', 'dir', 'getattr',
    'setattr', 'delattr', '__import__', '_getframe', 'currentframe', '__dict__',
    '__code__', '__closure__', '__globals__', '__annotations__', '__qualname__',
    '__getattribute__', 'f_locals', 'f_globals', 'gi_frame', 'cr_frame',
    'getsource', 'getsourcelines', 'findsource', 'getfile', 'getsourcefile',
    'getframeinfo', 'getouterframes', 'getinnerframes', 'stack', 'trace',
    'extract_stack', 'extract_tb', 'format_stack', 'format_tb', 'format_exc',
    'print_stack', 'print_tb', 'print_exc', 'StackSummary', 'TracebackException',
    'getline', 'getlines', '__file__',
}
FORMATTED_STRINGS = (ast.JoinedStr,) + ((ast.TemplateStr,) if hasattr(ast, 'TemplateStr') else ())
OPAQUE = (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp) + FORMATTED_STRINGS


def record(text):
    def unsupported(reason):
        return {'variables': [], 'unsafe': True, 'reason': reason}
    if not text.isascii():
        return unsupported('non_ascii')
    tree = ast.parse(text)
    if any(isinstance(node, (ast.Try, ast.TryStar)) for node in ast.walk(tree)):
        return unsupported('exception_handler_observability')
    table = symtable.symtable(text, 'candidate.py', 'exec')
    reserved = set(keyword.kwlist) | set(keyword.softkwlist) | {'self', 'cls'}
    tables = []

    def collect(t):
        tables.append(t)
        for s in t.get_symbols():
            if (t.get_type() != 'function' or s.is_global() or s.is_nonlocal()
                    or s.is_free() or s.is_imported() or s.is_namespace()
                    or s.is_parameter()):
                reserved.add(s.get_name())
        for child in t.get_children():
            collect(child)
    collect(table)
    for n in ast.walk(tree):
        annotations = []
        if isinstance(n, (ast.arg, ast.AnnAssign)) and n.annotation is not None:
            annotations.append(n.annotation)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None:
            annotations.append(n.returns)
        for annotation in annotations:
            reserved.update(child.id for child in ast.walk(annotation) if isinstance(child, ast.Name))
        if isinstance(n, ast.Name) and n.id in REFLECTION:
            return unsupported('reflection')
        if isinstance(n, ast.alias) and n.name.rsplit('.', 1)[-1] in REFLECTION:
            return unsupported('reflection_import')
        if isinstance(n, ast.Attribute):
            reserved.add(n.attr)
            if n.attr in REFLECTION:
                return unsupported('reflection')
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            reserved.add(n.name)
            if n.decorator_list or getattr(n, 'type_params', []):
                return unsupported('decorator_or_type_parameters')
        if isinstance(n, ast.keyword):
            if n.arg is None:
                return unsupported('keyword_expansion')
            reserved.add(n.arg)
        if isinstance(n, ast.ExceptHandler) and n.name:
            reserved.add(n.name)
        if isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name:
            reserved.add(n.name)
        if isinstance(n, ast.MatchMapping) and n.rest:
            reserved.add(n.rest)
        if isinstance(n, OPAQUE):
            for child in ast.walk(n):
                if isinstance(child, ast.Name):
                    reserved.add(child.id)
                if isinstance(child, ast.arg):
                    reserved.add(child.arg)
    offsets = [0] + [match.end() for match in re.finditer(r'\r\n|\r|\n', text)]
    spans = {}
    ownership = {}
    used_children = set()

    def child_table(parent, node, kind):
        children = [t for t in parent.get_children()
                    if t.get_type() == kind and t.get_name() == node.name
                    and t.get_lineno() == node.lineno and t.get_id() not in used_children]
        if len(children) != 1:
            raise ValueError('ambiguous AST/symtable scope mapping')
        child = children[0]
        used_children.add(child.get_id())
        return child

    def visit(node, scope):
        if isinstance(node, OPAQUE):
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Defaults execute in the defining scope; annotation names are fixed.
            # Parameters stay fixed, preserving the public keyword convention.
            for expr in node.args.defaults + [x for x in node.args.kw_defaults if x is not None]:
                visit(expr, scope)
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                if arg.annotation:
                    visit(arg.annotation, scope)
            for arg in (node.args.vararg, node.args.kwarg):
                if arg and arg.annotation:
                    visit(arg.annotation, scope)
            if node.returns:
                visit(node.returns, scope)
            inner = child_table(scope, node, 'function')
            for body in node.body:
                visit(body, inner)
            return
        if isinstance(node, ast.ClassDef):
            for expr in node.bases:
                visit(expr, scope)
            for kw in node.keywords:
                visit(kw.value, scope)
            inner = child_table(scope, node, 'class')
            for body in node.body:
                visit(body, inner)
            return
        if isinstance(node, ast.Name):
            # Annotation scopes differ across CPython versions. Every annotation
            # identifier is fixed globally, so no annotation lookup is needed.
            if node.id in reserved:
                return
            symbol = scope.lookup(node.id)
            if scope.get_type() == 'function' and symbol.is_local() and node.id not in reserved:
                key = (scope.get_id(), node.id)
                start = offsets[node.lineno - 1] + node.col_offset
                assert text[start:start + len(node.id)] == node.id
                spans.setdefault(key, set()).add((start, start + len(node.id)))
                ownership[key] = (scope.get_lineno(), scope.get_name())
        for child in ast.iter_child_nodes(node):
            visit(child, scope)
    try:
        visit(tree, table)
    except (KeyError, ValueError):
        return unsupported('scope_mapping')
    except AssertionError:
        return unsupported('scope_mapping_assert')
    # Global reservations deliberately exclude captured spelling from every
    # scope. Remaining eligible locals cannot have an edited cross-scope use.
    ordered = sorted(spans, key=lambda k: (min(spans[k]), k[1]))
    variables = []
    for i, key in enumerate(ordered):
        variables.append({'id': i, 'name': key[1], 'eligible': True,
                          'spans': sorted(spans[key]), 'forbidden': sorted(reserved),
                          'neighbors': [j for j, other in enumerate(ordered)
                                        if other[0] == key[0] and j != i],
                          'scope': list(ownership[key])})
    return {'variables': variables, 'unsafe': False, 'reason': None}


def validate_rewrite(original, rewritten, original_record):
    """Check syntax/AST identity except exact recorded Name spans, and name graph.

This is structural validation, not universal behavior equivalence. Runtime
qualification remains mandatory. Returns the final color vector.
"""
    before, after = ast.parse(original), ast.parse(rewritten)
    compile(after, 'candidate.py', 'exec')
    starts = [0] + [match.end() for match in re.finditer(r'\r\n|\r|\n', original)]
    owner = {}
    variables = original_record['variables']
    for variable in variables:
        for span in variable['spans']:
            assert tuple(span) not in owner, 'overlapping Name ownership'
            owner[tuple(span)] = variable['id']
    colors = [None] * len(variables)
    seen = set()

    def compare(a, b):
        assert type(a) is type(b), 'AST type changed'
        if isinstance(a, ast.Name):
            start = starts[a.lineno - 1] + a.col_offset
            span = (start, start + len(a.id))
            vid = owner.get(span)
            if vid is not None:
                seen.add(span)
                assert colors[vid] in (None, b.id), 'inconsistent binding spelling'
                colors[vid] = b.id
                assert type(a.ctx) is type(b.ctx), 'Name context changed'
                return
        if isinstance(a, ast.AST):
            af, bf = list(ast.iter_fields(a)), list(ast.iter_fields(b))
            assert [k for k, _ in af] == [k for k, _ in bf], 'AST fields changed'
            for (_, av), (_, bv) in zip(af, bf):
                compare(av, bv)
        elif isinstance(a, list):
            assert len(a) == len(b), 'AST list length changed'
            for av, bv in zip(a, b):
                compare(av, bv)
        else:
            assert a == b, 'nonbinding AST content changed'
    compare(before, after)
    assert seen == set(owner), 'record contains unmatched AST spans'
    for v in variables:
        color = colors[v['id']]
        assert color is not None and color.isidentifier(), 'invalid identifier'
        assert color not in keyword.kwlist and color not in keyword.softkwlist
        assert color not in v['forbidden'], 'reserved identifier'
        assert all(color != colors[j] for j in v['neighbors']), 'scope collision'
    final_record = record(rewritten)
    assert not final_record['unsafe'] or rewritten == original, 'new unsupported scope'
    return colors
