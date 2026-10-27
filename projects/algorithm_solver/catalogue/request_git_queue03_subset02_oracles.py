"""Source-blind node semantics only; no candidate node adapter is assumed.

Level-order arrays (tree) and value arrays (list) are explicit oracle wire
encodings, NOT claims about either language's actual candidate interface.
Existing native-node observers and identity/effect contracts need later review.
"""
from collections import deque
from itertools import product
import json
import random

from . import imported_qualification as q
from .request_git_queue03_oracles import integer, ints

IDS = (2265,2326)
PARAMETERS = {2265: ('root',),2326: ('m','n','head')}
TITLES = {2265: 'Count Nodes Equal to Average of Subtree',2326: 'Spiral Matrix IV'}
DEFINITION_SHA256 = {2265:'9c299f2b4dc6030f39fc8d9971986a2057437ad936983361d47e14cd96ce9ca0',
                     2326:'eeb3948fd2b48f47f9019cd9b2c30e13fdeec5b9fbce65aa8628fcfeabff94ba'}
SCOPE = {
    'evidence':'Exposed development, finite semantic oracle evidence only; not fresh confirmation or native-node qualification.',
    'wire':'2265 canonical compact breadth-first level-order values/nulls without trailing nulls;2326 finite list value sequence. Each positional nonnull is a distinct node; no cycles or shared parents.',
    'full_domain':'All rooted binary trees with1..1000 nodes and values0..1000; all positive matrix dimensions witharea<=100000 and nonempty finite lists length<=area,values0..1000. Wire validation is separately declared and is not a native interface claim.',
    'effects_alias':'Neither task requires input mutation. Native node identity, alias sharing, cyclic input rejection and linked traversal must be checked in the existing observer later.2326 output matrix freshness and independent row identities are not established by these value-only cases.',
    'numeric':'2265 uses exact nonnegative integer sums and floor division, output1..1000.2326 output strict integer cells in-1..1000, exact dimensions. All fit safe JS integer range.',
    'complexity':'Brute descendant scans on small trees; perimeter enumeration on small matrices. Large shapes have explicit construction-based answers. Native stack, time and memory behavior remains untested.',
    'interfaces':'Actual source SHA256, exported entrypoints and native TreeNode/ListNode adapter shapes unresolved. These cases must not be fed directly to unreviewed candidates.',
}


def tree_nodes(values):
    if type(values) is not list or not values or values[0] is None or values[-1] is None:
        raise ValueError('canonical nonempty tree wire required')
    if len(values)>1999 or any(x is not None and not integer(x,0,1000) for x in values):
        raise ValueError('tree value or wire bound')
    nodes=[values[0]]
    children=[[]]
    pending=deque([0])
    pos=1
    while pending and pos<len(values):
        parent=pending.popleft()
        for _ in range(2):
            if pos==len(values):
                break
            value=values[pos]
            pos+=1
            if value is not None:
                child=len(nodes)
                nodes.append(value)
                children.append([])
                children[parent].append(child)
                pending.append(child)
    if pos != len(values) or len(nodes)>1000:
        raise ValueError('unreachable node or too many nodes')
    return nodes,children


def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=len(PARAMETERS[pid]):
        raise ValueError('unsupported identity or ordered arguments')
    if pid==2265:
        tree_nodes(args[0])
    else:
        m,n,head=args
        if not (integer(m,1,100000) and integer(n,1,100000) and m*n<=100000 and ints(head,0,1000,1,m*n)):
            raise ValueError('outside full matrix/list domain')


def spiral_coordinates(m,n):
    """Peel disjoint ring perimeters, independent of moving-turn simulation."""
    coordinates=[]
    top,left,bottom,right=0,0,m-1,n-1
    while top<=bottom and left<=right:
        coordinates.extend((top,c) for c in range(left,right+1))
        coordinates.extend((r,right) for r in range(top+1,bottom+1))
        if top<bottom:
            coordinates.extend((bottom,c) for c in range(right-1,left-1,-1))
        if left<right:
            coordinates.extend((r,left) for r in range(bottom-1,top,-1))
        top+=1
        left+=1
        bottom-=1
        right-=1
    return coordinates


def expected(pid,args):
    validate(pid,args)
    if pid==2265:
        nodes,children=tree_nodes(args[0])
        if len(nodes)>40:
            raise ValueError('reference bound, not domain restriction')
        answer=0
        for root,value in enumerate(nodes):
            descendants=[]
            stack=[root]
            while stack:
                node=stack.pop()
                descendants.append(nodes[node])
                stack.extend(children[node])
            answer+=sum(descendants)//len(descendants)==value
        return answer
    m,n,head=args
    if m*n>200:
        raise ValueError('reference bound, not domain restriction')
    result=[[-1]*n for _ in range(m)]
    for (r,c),value in zip(spiral_coordinates(m,n),head):
        result[r][c]=value
    return result


EXAMPLES={2265:[([[4,8,5,0,1,None,6]],5),([[1]],1)],
          2326:[([3,5,[3,0,2,6,8,1,7,9,4,2,5,5,0]],[[3,0,2,6,8],[5,0,-1,-1,1],[5,2,4,9,7]]),
                ([1,4,[0,1,2]],[[0,1,2,-1]])]}


def _generate_cases(pid):
    cases,categories=[],[]
    sentinel=object()
    rng=random.Random(202610271842+pid)
    def add(args,category,answer=sentinel):
        validate(pid,args)
        cases.append({'args':args,'expected':expected(pid,args) if answer is sentinel else answer,'compare':'return'})
        categories.append(category)
    for args,answer in EXAMPLES[pid]:
        if not q.exact(expected(pid,args),answer):
            raise AssertionError('public example discrepancy')
        add(args,'pinned_public_example',answer)
    if pid==2265:
        for width in range(1,7):
            for values in product((0,1,3),repeat=width):
                add([list(values)],'exhaustive_complete_prefix_tree_values')
        for _ in range(200):
            target=rng.randrange(1,30)
            wire=[rng.randrange(1001)]
            pending=1
            count=1
            while pending and count<target:
                pending-=1
                for _ in range(2):
                    if count<target and (pending==0 or rng.randrange(3)):
                        wire.append(rng.randrange(1001))
                        pending+=1
                        count+=1
                    else:
                        wire.append(None)
            while wire[-1] is None:
                wire.pop()
            add([wire],'seeded_irregular_tree_shapes')
        add([[0]*1000],'analytic_maximum_complete_prefix_equal_values',1000)
        add([[1000]+[x for _ in range(999) for x in (None,1000)]],'analytic_maximum_height_right_chain',1000)
        add([[0]+[1000]*999],'analytic_root_below_equal_descendants',999)
    else:
        for m in range(1,7):
            for n in range(1,7):
                for count in range(1,m*n+1):
                    add([m,n,list(range(count))],'exhaustive_small_dimensions_and_fill_lengths')
        for values in product((0,1,1000),repeat=4):
            add([2,2,list(values)],'exhaustive_small_matrix_values')
        for _ in range(100):
            m,n=rng.randrange(1,14),rng.randrange(1,14)
            add([m,n,[rng.randrange(1001) for _ in range(rng.randrange(1,m*n+1))]],'seeded_rectangular_spirals')
        add([1,100000,[1000]*100000],'analytic_maximum_horizontal_full_list',[[1000]*100000])
        add([100000,1,[0]],'analytic_maximum_vertical_single_node',[[0]]+[[-1] for _ in range(99999)])
        add([400,250,[0]*100000],'analytic_maximum_area_full_constant',[ [0]*250 for _ in range(400)])
        matrix=[[-1]*250 for _ in range(400)]
        matrix[0][0]=1000
        add([400,250,[1000]],'analytic_maximum_area_single_node',matrix)
    return cases,categories


def build_cases(pid,statement):
    if pid not in IDS or type(statement) is not bytes or q.sha(statement)!=DEFINITION_SHA256[pid]:
        raise ValueError('exact freshly gated public definition required')
    definition=json.loads(statement)
    if definition['problem_id']!=pid or f'{pid}. {TITLES[pid]}' not in str(definition['web_result']):
        raise ValueError('definition identity mismatch')
    cases,categories=_generate_cases(pid)
    if len(q.encoded(cases))>q.MAX_FILE:
        raise ValueError('unchanged file cap exceeded')
    for _,batch in q.batches(cases):
        for language in ('python','javascript'):
            projected=sum(len(q.encoded({'i':i,'result':c['expected'],'result_type':q.expected_type(c['expected'],language),
                                         'args_before':c['args'],'args_after':c['args'],'alias_edges':[]})) for i,c in enumerate(batch))
            if projected+len(q.encoded({'done':len(batch)}))+1>q.LIMITS['max_output_bytes']:
                raise ValueError('unchanged output cap exceeded')
    return cases,categories
