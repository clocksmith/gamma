"""Opt-in proposal heuristic: skip statically unreachable numeric branches.

This is not a correctness rule: correct programs can contain dead branches.
Accepted controls are never filtered. Unknown bounds cause no rejection. The
analysis reads only the proposed typed graph, not examples, labels or targets.
"""
from __future__ import annotations


def unreachable_numeric_guard(program):
    def statements(body):
        for statement in body:
            yield statement
            for field in ('body', 'then', 'else'):
                yield from statements(statement.get(field, []))

    all_statements = list(statements(program['body']))
    # Only top-level mutable integer bindings get inductive global bounds.
    # Every possible write must preserve a lower bound; one unknown write
    # invalidates it, including writes nested under branches or loops.
    invariants = {}
    for declaration in program['body']:
        value = declaration.get('value', {})
        if declaration['op'] != 'var' or type(value.get('literal')) is not int:
            continue
        name = declaration['name']; constants = [value['literal']]
        safe = True
        for statement in all_statements:
            if statement['op'] != 'set' or statement['name'] != name:
                continue
            value = statement['value']
            if type(value.get('literal')) is int:
                constants.append(value['literal'])
            elif value.get('op') == 'add':
                a,b = value['args']
                if a == {'ref':name} and type(b.get('literal')) is int and b['literal'] >= 0:
                    continue
                if b == {'ref':name} and type(a.get('literal')) is int and a['literal'] >= 0:
                    continue
                safe = False; break
            else:
                safe = False; break
        if safe:
            invariants[name] = min(constants)

    def lower(value, env):
        if type(value.get('literal')) is int:
            return value['literal']
        if 'ref' in value:
            return env.get(value['ref'])
        if value.get('op') == 'add':
            a,b = [lower(v,env) for v in value['args']]
            return a+b if a is not None and b is not None else None
        return None

    def intersect(left, right):
        return {name:min(bound,right[name]) for name,bound in left.items() if name in right}

    def walk(body, env, path):
        env = dict(env)
        for index, statement in enumerate(body):
            at = path+[index]; op = statement['op']
            if op in ('var','let','set'):
                bound = lower(statement['value'],env)
                env.pop(statement['name'],None)
                if bound is not None:
                    env[statement['name']] = bound
            elif op == 'for':
                modified = {s['name'] for s in statements(statement['body']) if s['op']=='set'}
                loop_env = {k:v for k,v in env.items() if k not in modified and k != statement['item']}
                loop_env.update({k:invariants[k] for k in modified if k in invariants})
                failure, after = walk(statement['body'],loop_env,at+['body'])
                if failure:
                    return failure,env
                # A loop may run zero times or any permitted number of times.
                env = intersect(env,after)
            elif op == 'if':
                condition = statement['condition']
                if condition.get('op') in ('lt','eq'):
                    a,b = condition['args']; bound = lower(a,env)
                    cutoff = b.get('literal')
                    if (bound is not None and type(cutoff) is int and statement['then']
                            and (cutoff <= bound if condition['op']=='lt' else cutoff < bound)):
                        return dict(reason='provably_unreachable_then',path=at,
                                    comparison=condition['op'],lower_bound=bound,cutoff=cutoff),env
                failure,left = walk(statement['then'],env,at+['then'])
                if failure:
                    return failure,env
                failure,right = walk(statement['else'],env,at+['else'])
                if failure:
                    return failure,env
                env = intersect(left,right)
            elif op in ('call','recipe'):
                env.pop(statement['out'],None)
        return None,env

    return walk(program['body'],{},['body'])[0]
