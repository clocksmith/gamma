"""Versioned, deliberately bounded AST enforcement. No role inference or renaming."""
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tokenize

SEMANTIC_FIELDS = ('input_domain', 'numeric', 'strings', 'output_order', 'mutation',
                   'aliasing', 'algorithm', 'complexity', 'complexity_review', 'exceptions')


def check_semantics(document):
    errors = []
    if document.get('schema') != 'algsolve.corpus-semantics.v1':
        errors.append('semantic schema mismatch')
    for key in SEMANTIC_FIELDS:
        if not isinstance(document.get(key), str) or not document[key].strip():
            errors.append('missing semantic declaration: ' + key)
    # Presence is enforced, truth is established by review and execution evidence.
    return errors


def python_analysis(source, policy, entry, mapping=None):
    try:
        tree = ast.parse(source)
        compile(tree, '<corpus-candidate>', 'exec')  # Validate only; never execute.
    except SyntaxError as error:
        return dict(formatted=source, bindings={}, helpers={}, captures=[],
                    errors=['syntax failure: ' + str(error)])
    formatted = ast.unparse(tree) + '\n'
    errors, bindings, references, helpers = [], {}, [], {}
    if any(not isinstance(n, (ast.FunctionDef, ast.ClassDef)) for n in tree.body):
        errors.append('module body supports only unconditional function and adapter declarations')
    forbidden = (ast.Global, ast.Nonlocal, ast.Lambda, ast.ListComp, ast.SetComp,
                 ast.DictComp, ast.GeneratorExp, ast.AsyncFunctionDef,
                 ast.Import, ast.ImportFrom, ast.ExceptHandler, ast.Match,
                 ast.With, ast.AsyncWith, ast.AsyncFor, ast.NamedExpr,
                 ast.Delete, ast.Yield, ast.YieldFrom, ast.Await)
    if any(isinstance(n, forbidden) for n in ast.walk(tree)):
        errors.append('unsupported scope construct; reviewed extension required')
    if any(t.type == tokenize.COMMENT for t in tokenize.generate_tokens(io.StringIO(source).readline)):
        errors.append('comments require explicit preservation review before AST formatting')
    scopes = {'module': {'parent': None, 'kind': 'module', 'names': {}}}
    public_path = 'module/Solution/' + entry['method']
    adapters = []

    def bind(scope, name, node):
        previous = scopes[scope]['names'].get(name)
        if previous is not None and (isinstance(previous, (ast.FunctionDef, ast.ClassDef))
                                    or isinstance(node, (ast.FunctionDef, ast.ClassDef))):
            errors.append('protected callable binding reassigned: ' + name)
        scopes[scope]['names'].setdefault(name, node)

    def visit(node, scope):
        if isinstance(node, ast.ClassDef):
            bind(scope, node.name, node)
            child = scope + '/' + node.name
            if child in scopes:
                errors.append('duplicate scope: ' + child)
                return
            scopes[child] = {'parent': scope, 'kind': 'class', 'names': {}}
            if scope != 'module' or node.name != 'Solution' or node.bases or node.decorator_list or node.keywords:
                errors.append('only the plain Solution adapter class is supported')
            if len(node.body) != 1 or not isinstance(node.body[0], ast.FunctionDef):
                errors.append('Solution must contain only its thin adapter')
            for item in node.body:
                visit(item, child)
            return
        if isinstance(node, ast.FunctionDef):
            bind(scope, node.name, node)
            child = scope + '/' + node.name
            if child in scopes:
                errors.append('duplicate scope: ' + child)
                return
            scopes[child] = {'parent': scope, 'kind': 'function', 'names': {}}
            params = [arg.arg for arg in node.args.args]
            if node.args.posonlyargs or node.args.kwonlyargs or node.args.vararg or node.args.kwarg or node.args.defaults or node.decorator_list:
                errors.append('unsupported function signature: ' + child)
            if child == public_path:
                adapters.append(node)
                if params != ['self'] + entry['params']:
                    errors.append('public signature mismatch')
                call = node.body[0].value if len(node.body) == 1 and isinstance(node.body[0], ast.Return) else None
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                        and call.func.id == entry['internal'] and not call.keywords
                        and [arg.id if isinstance(arg, ast.Name) else None for arg in call.args] == entry['params']):
                    errors.append('adapter must forward exact positional arguments once')
            else:
                helpers[node.name] = params
                if policy['helpers'].get(node.name, {}).get('params') != params:
                    errors.append('helper signature mismatch: ' + node.name)
            for arg in node.args.args:
                bind(child, arg.arg, arg)
                if arg.annotation is None:
                    errors.append('missing parameter type: ' + child + ':' + arg.arg)
            # Conventional self is the only untyped parameter exception.
            if child == public_path:
                errors[:] = [e for e in errors if e != 'missing parameter type: ' + child + ':self']
            if node.returns is None:
                errors.append('missing return type: ' + child)
            for item in node.body:
                visit(item, child)
            return
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                bind(scope, node.id, node)
            elif isinstance(node.ctx, ast.Load):
                references.append((scope, node.id, node.lineno))
                if node.id == 'Solution':
                    errors.append('adapter class cannot be referenced or mutated by candidate code')
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            root = node.value
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name) and root.id in policy['helpers']:
                errors.append('helper properties cannot be mutated')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            spec = policy['helpers'].get(node.func.id)
            if spec and (node.keywords or any(isinstance(arg, ast.Starred) for arg in node.args)
                         or len(node.args) != len(spec['params'])):
                errors.append('helper positional arity mismatch: ' + node.func.id)
            if node.func.id in ('eval', 'exec', 'globals', 'locals'):
                errors.append('dynamic binding not supported')
        for item in ast.iter_child_nodes(node):
            visit(item, scope)

    visit(tree, 'module')

    def resolve(scope, name):
        current = scope
        while current:
            if name in scopes[current]['names']:
                return current
            current = scopes[current]['parent']
            while current and scopes[current]['kind'] == 'class':
                current = scopes[current]['parent']
        return None

    captures = []
    for scope, info in scopes.items():
        for name in info['names']:
            if (name == 'Solution' and scope == 'module'
                    and isinstance(info['names'][name], ast.ClassDef)) or scope == public_path or info['kind'] == 'class':
                continue
            key = scope + ':' + name
            role = next((r for r, canonical in policy['roles'].items() if canonical == name), None)
            bindings[key] = {'name': name, 'role': role, 'references': 0}
            parent = info['parent']
            if parent and resolve(parent, name):
                errors.append('live binding shadowing: ' + key)
    for scope, name, line in references:
        owner = resolve(scope, name)
        key = str(owner) + ':' + name
        if key in bindings:
            bindings[key]['references'] += 1
            if owner != scope:
                captures.append({'binding': key, 'reference_line': line})
    if len(adapters) != 1:
        errors.append('missing exact Solution method adapter')
    internal = scopes['module']['names'].get(entry['internal'])
    if not isinstance(internal, ast.FunctionDef) or entry['internal'] not in policy['helpers']:
        errors.append('adapter internal must resolve to a registered module function')
    allowed_globals = {'ListNode', 'Optional', 'list', 'tuple', 'int', 'str', 'bool',
                       'len', 'range', 'ord', 'enumerate'}
    for scope, name, line in references:
        if resolve(scope, name) is None and name not in allowed_globals:
            errors.append('unsupported unresolved reference: ' + name)
    if mapping is not None:
        if mapping.get('schema') != 'algsolve.reviewed-bindings.v1' or not mapping.get('reviewed_by'):
            errors.append('reviewed binding mapping required')
        if mapping.get('source_sha256') != hashlib.sha256(source.encode()).hexdigest():
            errors.append('stale reviewed mapping')
        for key, binding in bindings.items():
            role = mapping.get('bindings', {}).get(key)
            if not role or policy['roles'].get(role) != binding['name']:
                errors.append('unreviewed or noncanonical binding: ' + key)
        for key in mapping.get('bindings', {}):
            if key not in bindings:
                errors.append('stale binding: ' + key)
        if source != formatted:
            errors.append('noncanonical formatting')
    return dict(formatted=formatted, bindings=bindings, helpers=helpers, captures=captures, errors=errors)


def analyze(source, language, policy, entry, mapping=None):
    if language == 'python':
        return python_analysis(source, policy, entry, mapping)
    request = dict(source=source, policy=policy, entry=entry, mapping=mapping)
    process = subprocess.run(['node', str(Path(__file__).with_name('corpus_standard_js.cjs'))],
                             input=json.dumps(request), text=True, capture_output=True, timeout=10)
    if not process.stdout:
        raise RuntimeError(process.stderr)
    return json.loads(process.stdout)


def check_candidate(source, language, policy, entry, mapping, semantics):
    result = analyze(source, language, policy, entry, mapping)
    if mapping is None:
        result['errors'].append('reviewed binding mapping required')
    result['errors'].extend(check_semantics(semantics))
    second = analyze(result.get('formatted', source), language, policy, entry)
    if second.get('formatted') != result.get('formatted'):
        result['errors'].append('formatter is not idempotent')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--language', choices=['javascript', 'python'], required=True)
    parser.add_argument('--policy', type=Path, required=True)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--semantics', type=Path, required=True)
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text())['languages'][args.language]
    contract = json.loads(args.contract.read_text())
    entry = dict(contract['entry'], internal=contract['internal'][args.language])
    result = check_candidate(args.source.read_text(), args.language, policy, entry,
                             json.loads(args.mapping.read_text()), json.loads(args.semantics.read_text()))
    print(json.dumps({'passed': not result['errors'], 'errors': result['errors'],
                      'bindings_checked': len(result.get('bindings', {}))}, indent=2))
    raise SystemExit(bool(result['errors']))
