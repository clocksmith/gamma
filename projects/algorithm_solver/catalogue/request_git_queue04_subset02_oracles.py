"""Queue04 node/state semantic wires, NOT native candidate interfaces.

No candidate access/execute route. Identity, state persistence and observer
adapters remain blocking gaps even when all value-level cases are correct.
"""
from collections import deque
from itertools import permutations, product
import random

from . import imported_qualification as q
from .imported_clean_domains import integer, ints

IDS = (2415,2424,2471)
WIRE_PARAMETERS = {2415:('perfect_tree_level_values',),2424:('n','operations'),2471:('compact_tree_levelorder',)}
DEFINITION_SHA256 = {2415:'dad0a43c297a18c80d6510e9152a7d2c8d1496c0def3497071d4718820e7a6f8',
                     2424:'f6bfa99e4af5a25eaf3c47b27bab0951fc0928e0ff9a34e23f716a0ad911362a',
                     2471:'3766f9dde362ff10561f6aad07ee07d11bdcc73f0e7b5d6c1dd6a8c89dc3845f'}
SCOPE = {
    'wire':'2415 complete breadth-first values;2471 canonical compact breadth-first values/nulls without trailing nulls, each value position denotes one distinct node;2424 n plus operations, each upload is [upload,video] and query is [longest], outputs correspond only to operations, not constructor.',
    'interfaces':'All actual candidate interfaces, constructors/exports and source SHA256 unknown. These semantic wires must not be passed to unreviewed native candidates.',
    'effects_alias':'2415 requires original root returned with odd-level node values reversed, not a fresh-array implementation; topology and identities must remain those of input tree. 2471 supplies only minimum swap count; native effects and identity policy need review. 2424 requires persistent per-instance state and instance isolation; this pure transcript reference does not establish either for candidates.',
    'numeric':'Exact Python ints excluding bool; all values/counts within stated ranges. No float/Unicode/native runtime extrapolation.',
    'complexity':'Finite bounded references and separate analytic shapes. Native time, memory, recursion/stack and stateful operation performance unmeasured.',
    'qualification':'Exposed development semantic evidence only, not fresh confirmation or candidate qualification.',
}


def tree_levels(wire):
    if type(wire) is not list or not wire or wire[0] is None or wire[-1] is None or len(wire)>199999:
        raise ValueError('canonical nonempty compact tree wire required')
    if any(v is not None and not integer(v,1,100000) for v in wire):
        raise ValueError('node value outside domain')
    values=[v for v in wire if v is not None]
    if not 1<=len(values)<=100000 or len(set(values))!=len(values):
        raise ValueError('unique node values and count required')
    levels=[];queue=deque([(wire[0],0)]);pos=1
    while queue:
        value,depth=queue.popleft()
        if depth==len(levels):levels.append([])
        levels[depth].append(value)
        for _ in range(2):
            if pos<len(wire):
                child=wire[pos];pos+=1
                if child is not None:queue.append((child,depth+1))
    if pos!=len(wire):raise ValueError('orphan child in wire')
    return levels


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(WIRE_PARAMETERS[pid]):
        raise ValueError('unsupported identity or semantic wire shape')
    if pid==2415:
        a=args[0]
        if not (ints(a,0,100000,1,2**14) and (len(a)+1)&len(a)==0):
            raise ValueError('complete perfect-tree values required')
    elif pid==2471:
        tree_levels(args[0])
    else:
        n,ops=args
        if not integer(n,1,100000) or type(ops) is not list or not 1<=len(ops)<=200000:
            raise ValueError('constructor or operation-count domain')
        uploaded=set();queries=0
        for op in ops:
            if type(op) is not list or not op or type(op[0]) is not str:
                raise ValueError('operation wire')
            if op[0]=='upload' and len(op)==2 and integer(op[1],1,n) and op[1] not in uploaded:
                uploaded.add(op[1])
            elif op==['longest']:
                queries+=1
            else:raise ValueError('invalid operation or duplicate upload')
        if not queries:raise ValueError('at least one longest query required')


def _swap_distance(values):
    start=tuple(values);target=tuple(sorted(values));ready=deque([(start,0)]);seen={start}
    while ready:
        state,d=ready.popleft()
        if state==target:return d
        for i in range(len(state)):
            for j in range(i+1,len(state)):
                nxt=list(state);nxt[i],nxt[j]=nxt[j],nxt[i];nxt=tuple(nxt)
                if nxt not in seen:seen.add(nxt);ready.append((nxt,d+1))


def expected(pid,args):
    validate(pid,args)
    if pid==2415:
        values=args[0]
        if len(values)>127:raise ValueError('reference bound, not full domain')
        result=[];queue=deque([(0,0)]);levels=[]
        while queue:
            index,depth=queue.popleft()
            if depth==len(levels):levels.append([])
            levels[depth].append(values[index])
            for child in (index*2+1,index*2+2):
                if child<len(values):queue.append((child,depth+1))
        for depth,level in enumerate(levels):result.extend(level[::-1] if depth%2 else level)
        return result
    if pid==2471:
        levels=tree_levels(args[0])
        if len(args[0])>63 or max(map(len,levels))>8:raise ValueError('reference bound, not full domain')
        return sum(_swap_distance(level) for level in levels)
    n,ops=args
    if n>30 or len(ops)>100:raise ValueError('reference bound, not full domain')
    uploaded=set();answer=[]
    for op in ops:
        if op[0]=='upload':uploaded.add(op[1]);answer.append(None)
        else:answer.append(next((i-1 for i in range(1,n+1) if i not in uploaded),n))
    return answer


EXAMPLES={2415:[([[2,3,5,8,13,21,34]],[2,5,3,8,13,21,34]),([[7,13,11]],[7,11,13]),
                ([[0,1,2,0,0,0,0,1,1,1,1,2,2,2,2]],[0,2,1,0,0,0,0,2,2,2,2,1,1,1,1])],
          2424:[([4,[['upload',3],['longest'],['upload',1],['longest'],['upload',2],['longest']]],[None,0,None,1,None,3])],
          2471:[([[1,4,3,7,6,8,5,None,None,None,None,9,None,10]],3),([[1,3,2,7,6,5,4]],3),([[1,2,3,4,5,6]],0)]}


def _generate_cases(pid):
    cases=[];categories=[];rng=random.Random(202610271846+pid);sentinel=object()
    def add(args,category,answer=sentinel):
        validate(pid,args);cases.append({'args':args,'expected':expected(pid,args) if answer is sentinel else answer,'compare':'return'});categories.append(category)
    for args,answer in EXAMPLES[pid]:
        if not q.exact(expected(pid,args),answer):raise AssertionError('public example mismatch')
        add(args,'pinned_public_example_semantic_wire',answer)
    if pid==2415:
        for n in (1,3,7):
            for a in product((0,1),repeat=n):add([list(a)],'exhaustive_small_perfect_binary_values')
        for _ in range(100):
            n=rng.choice((15,31,63,127));add([[rng.randrange(100001) for _ in range(n)]],'seeded_multilevel_reversal')
        n=16383
        add([[0]*n],'analytic_maximum_perfect_tree_equal_values',[0]*n)
        values=list(range(n));answer=[(3*(1<<((i+1).bit_length()-1))-3-i) if ((i+1).bit_length()-1)%2 else i for i in range(n)]
        add([values],'analytic_maximum_perfect_tree_heap_address_reflection',answer)
    elif pid==2424:
        for n in range(1,6):
            for count in range(n+1):
                for order in permutations(range(1,n+1),count):
                    ops=[['longest']]
                    for video in order:ops.extend((['upload',video],['longest']))
                    add([n,ops],'exhaustive_partial_upload_permutations_with_prefix_queries')
        for _ in range(60):
            n=rng.randrange(1,31);order=list(range(1,n+1));rng.shuffle(order);ops=[['longest']]
            for video in order:
                ops.append(['upload',video]);ops.extend([['longest'] for _ in range(rng.randrange(3))])
            add([n,ops],'seeded_repeated_queries_interleaved_uploads')
        add([100000,[['upload',100000],['longest'],['upload',1],['longest']]],'analytic_maximum_label_missing_prefix',[None,0,None,1])
        ops=[];answer=[]
        for video in range(1,25001):ops.extend((['upload',video],['longest']));answer.extend((None,video))
        add([100000,ops],'analytic_fitting_50000_stateful_operations',answer)
    else:
        for n in range(1,7):
            for a in permutations(range(1,n+1)):add([list(a)],'exhaustive_complete_prefix_unique_value_permutations')
        for _ in range(40):
            n=rng.randrange(1,16);values=rng.sample(range(1,100001),n);add([values],'seeded_distinct_level_swap_search')
        add([[i for v in range(1,100001) for i in ((v,) if v==1 else (None,v))]],'analytic_maximum_height_singletons',0)
        add([list(range(1,100001))],'analytic_maximum_sorted_level_values',0)
        add([list(range(100000,0,-1))],'analytic_maximum_reversed_level_values',49999)
    return cases,categories


def build_cases(pid,statement):
    if type(pid) is not int or pid not in IDS or type(statement) is not bytes or q.sha(statement)!=DEFINITION_SHA256[pid]:
        raise ValueError('exact freshly gated official definition required')
    cases,categories=_generate_cases(pid)
    if len(q.encoded(cases))>q.MAX_FILE:raise ValueError('unchanged file cap exceeded')
    for _,batch in q.batches(cases):
        for language in ('python','javascript'):
            size=sum(len(q.encoded({'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),'args_before':c['args'],'args_after':c['args'],'alias_edges':[]})) for i,c in enumerate(batch))
            if size+len(q.encoded({'done':len(batch)}))+1>q.LIMITS['max_output_bytes']:raise ValueError('unchanged output cap exceeded')
    return cases,categories
