"""Opt-in binding of an explicit absent-result integer to a return accumulator.

No target program or independent test supplies values. One public declaration
may bind one literal; the existing two-bit model search retains its four-public-
execution and .25-second total repair envelope. Default routes are unchanged.
"""
from __future__ import annotations
import copy
import re
import time

from .. import validate
from . import typed_codec
from .typed_correction import validate_codes
from .typed_guard_filter import unreachable_numeric_guard
from .typed_literal_repair import literal_search
from .typed_semantic_repair import run_semantic_route

_FALLBACK = re.compile(r'If there is no such [a-z][a-z ]{0,80},\s*return (-?\d+)',re.I)


def bind_absent_return(program, statement):
    requirements = re.split(r'\bExample\s*\d*\s*:',statement,maxsplit=1,flags=re.I)[0]
    clauses = [' '.join(s.split()) for s in re.split(r'[.!?\n]',requirements) if s.strip()]
    matches = [m for s in clauses if (m := _FALLBACK.fullmatch(s))]
    literal_returns = re.findall(r'\breturn\s+(-?\d+)\b',requirements,flags=re.I)
    if len(matches) != 1 or len(literal_returns) != 1 or set(program['return']) != {'ref'}:
        return None
    value = int(matches[0].group(1))
    if abs(value).bit_length() > 128:
        return None
    name = program['return']['ref']
    declarations = [s for s in program['body'] if s['op']=='var' and s['name']==name]
    if len(declarations)!=1 or type(declarations[0]['value'].get('literal')) is not int:
        return None
    original = declarations[0]['value']['literal']
    if value == original:
        return None
    def refs(node):
        if isinstance(node,dict):
            return node == {'ref':name} or any(refs(v) for v in node.values())
        return isinstance(node,list) and any(refs(v) for v in node)
    # Initial value has no role in control or computation, only in the final
    # answer when no conditional assignment has occurred.
    if refs(program['body']):
        return None
    writes=[]
    def visit(body,conditional=False):
        for s in body:
            if s['op']=='set' and s['name']==name:
                writes.append(conditional)
            for key in ('body','then','else'):
                visit(s.get(key,[]),conditional or key in ('then','else'))
    visit(program['body'])
    if not writes or not all(writes):
        return None
    result=copy.deepcopy(program)
    next(s for s in result['body'] if s['op']=='var' and s['name']==name)['value']['literal']=value
    return dict(graph=result,name=name,before=original,after=value,
                declaration=matches[0].group(0),reason='explicit query absent-result contract; return-only accumulator')


def run_public_bound_route(control,problem,logits,encoding,identity,config,budget,*,judge=validate.judge_problem):
    started=time.perf_counter()
    binding=None
    if (control['decision']!='answered' and control['structurally_valid']
            and not control['infrastructure_failure'] and control['reason']=='public_failure'
            and problem.public_tests):
        binding=bind_absent_return(control['final_graph'],problem.statement)
    if binding is None:
        result=run_semantic_route(control,problem,logits,encoding,identity,config,budget,
                                  judge=judge,literal_filter=unreachable_numeric_guard)
        elapsed=time.perf_counter()-started
        result['timing']['public_binding_overhead_seconds']=elapsed-result['timing']['semantic_seconds']
        result['timing']['total_seconds']=control['timing']['total_seconds']+elapsed
        if (result['timing']['total_seconds']>budget or
                (result.get('semantic_repair') is not None and elapsed>config['wall_seconds'])):
            result.update(decision='abstain',reason='public_binding_budget')
        return result
    result=copy.deepcopy(control);result.update(route='public_bound_semantic',semantic_repair=None)
    graph=binding.pop('graph');result['public_literal_binding']=binding
    before=encoding.encode(control['final_graph']);after=encoding.encode(graph)
    changed=[i for i,(a,b) in enumerate(zip(before['bits'],after['bits'])) if a!=b]
    if len(changed)!=1 or any(before[k]!=after[k] for k in before if k!='bits'):
        raise ValueError('Public binding must change exactly one literal and no structure')
    slot=changed[0];codes=copy.deepcopy(control['correction']['final_codes'])
    if codes['bits'][slot]!=before['bits'][slot]:
        raise ValueError('Binding source differs from captured graph')
    codes['bits'][slot]=after['bits'][slot];binding['slot']=slot
    _,error=validate_codes(encoding,codes,[p[0] for p in problem.params])
    if error:raise ValueError('Invalid bound graph: '+error)
    def render(g):
        return typed_codec.render(typed_codec.encode(g,identity),identity,
                                 method=problem.entry['method'],params=[p[0] for p in problem.params])
    def evaluate(g,seconds):
        return judge(problem,render(g),problem.public_tests,wall_seconds=seconds).to_dict()
    remaining=budget-control['timing']['total_seconds']
    repair=literal_search(encoding,codes,logits['bits'],[p[0] for p in problem.params],config,evaluate,
                         deadline=started+min(remaining,config['wall_seconds']),candidate_filter=unreachable_numeric_guard,
                         captured_bits=control['correction']['final_codes']['bits'],frozen_slots=(slot,))
    final=repair.pop('graph');result['semantic_repair']=repair
    result['infrastructure_failure'] |= repair['infrastructure_failure']
    if final is not None:
        source=render(final)
        result.update(final_graph=final,graph_sha256=typed_codec.digest(typed_codec.encode(final,identity)),
                      source=source,source_sha256=typed_codec.digest(source),public=repair['attempts'][-1]['public'],
                      decision='answered',reason='public_binding_and_literal_passed')
    else:result['reason']=repair['reason']
    elapsed=time.perf_counter()-started
    result['timing']['public_binding_seconds']=elapsed
    result['timing']['total_seconds']=control['timing']['total_seconds']+elapsed
    if result['timing']['total_seconds']>budget or elapsed>config['wall_seconds']:
        result.update(decision='abstain',reason='public_binding_budget')
    return result
