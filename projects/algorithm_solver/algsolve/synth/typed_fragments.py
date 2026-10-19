"""Paused fit-only fragment prototype, preserved before the semantic-macro goal clarification.
No query route uses it; no solving qualification or promotion. No closures or resource ports."""
from __future__ import annotations

import copy
import re
import math
import time
from collections import Counter
from . import typed_program as ir, typed_recipes, typed_codec

LIMITS = dict(max_operations=16, max_ports=3, max_span=6, max_pieces=3,
              max_candidates=128, max_expansions=2048, wall_seconds=2.0)


def expr_type(e, scope):
    if 'ref' in e:
        return scope[e['ref']]
    if 'literal' in e:
        return 'bool' if type(e['literal']) is bool else 'int'
    return ir.pure_type(e['op'], [expr_type(a, scope) for a in e['args']], e['args'])


def declarations(body, initial):
    scope = dict(initial)
    for s in body:
        if s['op'] in ('let', 'var'):
            scope[s['name']] = expr_type(s['value'], scope)
        elif s['op'] == 'call':
            scope[s['out']] = ir.EFFECTS[s['operator']][1]
    return scope


def close_fragment(body, answer, scope):
    """Lift read-only free values. Reject writes to external cells/resources."""
    ports = {}
    def expr(e, local):
        if 'ref' in e:
            key = e['ref']
            if key not in local:
                ty = scope[key]
                if ir.resource(ty) or ty == 'unit':
                    raise ir.Invalid('A fragment cannot capture a resource')
                ports.setdefault(key, ty)
        elif 'op' in e:
            for a in e['args']:
                expr(a, local)
    def block(items, local):
        for s in items:
            op = s['op']
            if op in ('let', 'var', 'set'):
                if op == 'set' and s['name'] not in local:
                    raise ir.Invalid('A fragment cannot write an external cell')
                expr(s['value'], local)
                local.add(s['name'])
            elif op == 'call':
                for a in s['args']:
                    expr(a, local)
                local.add(s['out'])
            elif op == 'for':
                expr(s['in'], local)
                block(s['body'], local | {s['item']})
            elif op == 'if':
                expr(s['condition'], local)
                block(s['then'], set(local)); block(s['else'], set(local))
            else:
                raise ir.Invalid('Expand recipes before extraction')
    local = set()
    block(body, local); expr(answer, local)
    output = expr_type(answer, declarations(body, scope))
    if ir.resource(output) or output == 'unit':
        raise ir.Invalid('A fragment must return an ordinary value')
    program = dict(schema=ir.SCHEMA, parameters=list(ports), inputs=ports,
                   body=body, **{'return':answer}, output_type=output)
    # Existing validator enforces all port types, lexical scopes and resource rules.
    program = json_copy(program)
    ir.validate(program)
    canonical, mapping = ir.expanded(program, {})
    return canonical, {mapping[k]:k for k in ports}


def json_copy(value):
    import json
    return json.loads(json.dumps(value))


def build_index(fit, limits=None):
    limits = dict(LIMITS, **(limits or {}))
    if not fit or any(p['learning_split'] != 'development_fit' for p in fit):
        raise ValueError('Fragment extraction requires exclusively development-fit graphs')
    items, rejected = {}, Counter()
    for pair in fit:
        if typed_codec.digest(pair['target']) != pair['graph_sha256']:
            raise ValueError('Fit target hash mismatch')
        full, _ = ir.expanded(pair['target']['program'], typed_recipes.catalog())
        whole_size = sum(ir.operation_counts(full).values())
        def add(body, answer, scope, location, kind):
            try:
                fragment, roles = close_fragment(body, answer, scope)
                counts = ir.operation_counts(fragment); size = sum(counts.values())
                if not 0 < size < whole_size or size > limits['max_operations']:
                    raise ir.Invalid('Not a bounded proper subprogram')
                if not 0 < len(fragment['parameters']) <= limits['max_ports']:
                    raise ir.Invalid('Unsupported port count')
                key = typed_codec.digest(fragment)
                entry = items.setdefault(key, dict(id=key, program=fragment,
                    inputs=fragment['inputs'], output=fragment['output_type'], operations=counts,
                    effects=sorted({ir.EFFECTS[k][2] for k in counts if k in ir.EFFECTS}),
                    resource_policy='Resources are allocated inside each invocation and never cross ports',
                    qualification='Candidate subprogram extracted from a qualified fit graph; no standalone semantic qualification or promotion',
                    constants=[], provenance=[]))
                def literals(v):
                    if isinstance(v,dict):
                        if 'literal' in v: yield v['literal']
                        for c in v.values(): yield from literals(c)
                    elif isinstance(v,list):
                        for c in v: yield from literals(c)
                entry['constants'] = list(literals(fragment))
                entry['provenance'].append(dict(uid=pair['uid'], family=pair['problem_family'],
                    graph_sha256=pair['graph_sha256'], location=location, kind=kind,
                    port_roles=roles, statement=pair['input']['statement']))
            except (ir.Invalid, KeyError) as exc:
                rejected[str(exc)] += 1
        def expressions(e, scope, path, kind='expression'):
            if isinstance(e,dict) and 'op' in e and 'args' in e:
                add([], e, scope, path, kind)
                for i,a in enumerate(e['args']):
                    expressions(a, scope, path+f'/args/{i}')
        def block(body, initial, path):
            scopes = [dict(initial)]
            for s in body:
                scopes.append(declarations([s], scopes[-1]))
            for i,s in enumerate(body):
                scope = scopes[i]
                for key in ('value','in','condition'):
                    if key in s: expressions(s[key],scope,path+f'/{i}/{key}')
                for j,a in enumerate(s.get('args',[])):
                    expressions(a,scope,path+f'/{i}/args/{j}')
                if s['op']=='for':
                    child = dict(scope); child[s['item']] = expr_type(s['in'],scope)[1]
                    block(s['body'],child,path+f'/{i}/body')
                if s['op']=='if':
                    for branch in ('then','else'):block(s[branch],dict(scope),path+f'/{i}/{branch}')
                for end in range(i+1,min(len(body),i+limits['max_span'])+1):
                    span = body[i:end]; after = scopes[end]
                    names = [v.get('name') if v['op'] in ('let','var') else v.get('out') if v['op']=='call' else None for v in span]
                    for name in filter(None,names):
                        if not ir.resource(after[name]) and after[name]!='unit':
                            add(span,{'ref':name},scope,path+f'/{i}:{end}/return/{name}','block')
            return scopes[-1]
        final = block(full['body'], {k:ir.dtype(v) for k,v in full['inputs'].items()}, '/body')
        expressions(full['return'],final,'/return','return_expression')
    return dict(schema='algsolve.typed-fragments.v1',limits=limits,
                source_graphs=sorted(p['graph_sha256'] for p in fit),
                fragments=[items[k] for k in sorted(items)],rejected=dict(rejected))


def terms(text):
    return Counter(re.findall(r'[a-z]+',text.lower()))


def cosine(left,right):
    norm=math.sqrt(sum(v*v for v in left.values())*sum(v*v for v in right.values()))
    return sum(v*right.get(k,0) for k,v in left.items())/norm if norm else 0.


def rank_fragments(index, statement, guided):
    query=terms(statement)
    def key(f):
        score=max(cosine(query,terms(p['statement'])) for p in f['provenance']) if guided else 0.
        # All fragments remain eligible; ranking alone differs from unguided.
        terminal=any(p['kind']=='return_expression' for p in f['provenance'])
        return (-score, -int(terminal) if guided else 0, f['id'])
    return sorted(index['fragments'],key=key)


def assemble(term, inputs, output, index):
    ir.bounded_tree(term)
    fragments={f['id']:f for f in index['fragments']}
    body, recipes, trace = [], {}, []
    def emit(node):
        if set(node)=={'input'}:
            if node['input'] not in inputs:raise ir.Invalid('Unknown external binding')
            return {'ref':node['input']}
        if set(node)!={'fragment','args'} or node['fragment'] not in fragments:
            raise ir.Invalid('Unknown fragment term')
        f=fragments[node['fragment']]
        if typed_codec.digest(f['program'])!=f['id']:raise ir.Invalid('Fragment content changed')
        args=[emit(arg) for arg in node['args']]
        out=f'piece{len(body)}'; key=f'fragment{len(body)}'
        recipes[key]=f['program']
        body.append(dict(op='recipe',recipe=key,args=args,out=out))
        trace.append(dict(fragment=f['id'],binding=out,args=copy.deepcopy(args),provenance=f['provenance']))
        return {'ref':out}
    answer=emit(term)
    if len(body)>index['limits']['max_pieces']:raise ir.Invalid('Piece limit')
    program=json_copy(dict(schema=ir.SCHEMA,parameters=list(inputs),inputs=inputs,body=body,
                           **{'return':answer},output_type=output))
    ir.validate(program,recipes)
    expanded,_=ir.expanded(program,recipes)
    # Preserve the caller's external names after hygienic recipe expansion.
    rename={f'input{i}':name for i,name in enumerate(inputs)}
    def refs(v):
        if isinstance(v,dict):
            return {k:rename.get(x,x) if k=='ref' else refs(x) for k,x in v.items()}
        if isinstance(v,list):return [refs(x) for x in v]
        return v
    expanded=refs(expanded);expanded['parameters']=list(inputs);expanded['inputs']=json_copy(inputs)
    ir.validate(expanded)
    return expanded,trace


def candidates(index, inputs, output, statement, guided, stats, deadline):
    """Bounded backward typed tree assembly. All leaves are explicit input wires."""
    ranked=rank_fragments(index,statement,guided)
    by_type={}
    for f in ranked:by_type.setdefault(ir.dtype(f['output']),[]).append(f)
    input_types={k:ir.dtype(v) for k,v in inputs.items()}
    minimum={ty:0 for ty in input_types.values()}
    for _ in range(index['limits']['max_pieces']):
        for f in ranked:
            ports=[ir.dtype(v) for v in f['inputs'].values()]
            if all(t in minimum for t in ports):
                ty=ir.dtype(f['output']);minimum[ty]=min(minimum.get(ty,999),1+sum(minimum[t] for t in ports))
    def budget():
        return time.perf_counter()<deadline and stats['expansions']<index['limits']['max_expansions']
    def generate(ty,remaining):
        if not budget():return
        for name,t in input_types.items():
            if t==ty:yield {'input':name},0
        if remaining<1:return
        for f in by_type.get(ty,[]):
            if not budget():return
            ports=[ir.dtype(v) for v in f['inputs'].values()]
            if any(t not in minimum for t in ports) or 1+sum(minimum[t] for t in ports)>remaining:continue
            stats['expansions']+=1
            def arguments(i,left,args,cost):
                if not budget():return
                if i==len(ports):yield args,cost;return
                reserved=sum(minimum[t] for t in ports[i+1:])
                for term,n in generate(ports[i],left-reserved):
                    yield from arguments(i+1,left-n,args+[term],cost+n)
            for args,n in arguments(0,remaining-1,[],0):
                yield {'fragment':f['id'],'args':args},n+1
    seen=set()
    for term,pieces in generate(ir.dtype(output),index['limits']['max_pieces']):
        if not budget() or stats['candidates']>=index['limits']['max_candidates']:return
        if not pieces:continue
        digest=typed_codec.digest(term)
        if digest in seen:continue
        seen.add(digest);stats['candidates']+=1
        yield term
