"""Deterministic finite R references/cases, no candidate imports or expected answers."""
import ast
import hashlib
import html
import importlib.util
from itertools import product,permutations
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('r_source_blind_oracles',HERE/'oracles.py')
oracle=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(oracle)
IDS=oracle.IDS
ASSIGNED_IDS=oracle.ASSIGNED_IDS


def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def shared(a,b,tail):
    values=a+b+tail;nodes=[{'value':v,'next':None} for v in values];t=len(a)+len(b)
    for start,part in ((0,a),(len(a),b),(t,tail)):
        for i in range(start,start+len(part)-1):nodes[i]['next']=i+1
        if part and start!=t and tail:nodes[start+len(part)-1]['next']=t
    roots=[0 if a else t,len(a) if b else t]
    return {'__list_graph__':{'nodes':nodes,'argument_roots':roots}}


def balanced(values):
    if not values:return None
    mid=len(values)//2;return values[mid],balanced(values[:mid]),balanced(values[mid+1:])


def tree_marker(tree):
    values=[];queue=[tree] if tree else []
    for node in queue:
        if node is None:values.append(None)
        else:values.append(node[0]);queue.extend((node[1],node[2]))
    while values and values[-1] is None:values.pop()
    return {'__tree_node__':values}


def json_arrays(text):
    decoder=json.JSONDecoder();result=[];remaining=text.strip()
    for _ in range(2):
        start=remaining.find('[')
        if start<0:raise ValueError('official trace input arrays')
        value,end=decoder.raw_decode(remaining[start:]);result.append(value);remaining=remaining[start+end:].strip()
    return result


def official_inputs(directory,read_raw=None):
    contract=json.loads((HERE/'contracts.json').read_bytes());result={}
    for spec in contract['problems']:
        pid=spec['id']
        if spec['status']!='public-verified':continue
        path=Path(directory)/f'{pid}.json';raw=path.read_bytes() if read_raw is None else read_raw(pid,path)
        q=json.loads(raw)['data']['question'];pin=spec['definition']
        if hashlib.sha256(raw).hexdigest()!=pin['response_sha256'] or q['questionFrontendId']!=str(pid) or q['titleSlug']!=pin['slug'] or q['isPaidOnly'] is not False or hashlib.sha256(q['content'].encode()).hexdigest()!=pin['content_sha256']:raise ValueError('exact public R definition drift')
        body=html.unescape(re.sub('<[^>]*>',' ',q['content']));rows=[]
        for match in re.finditer(r'Input:?\s*(.*?)\s*Output:?' ,body,re.S):
            text=match[1]
            if pid in oracle.CLASSES:
                args=json_arrays(text)
                if pid==173:args[1][0][0]={'__tree_node__':args[1][0][0]}
            else:
                call=ast.parse('f('+re.sub(r'\bnull\b','None',text.strip())+')',mode='eval').body
                if not isinstance(call,ast.Call) or call.args:raise ValueError('official argument grammar')
                named={k.arg:ast.literal_eval(k.value) for k in call.keywords}
                if pid==147:args=[{'__list_node__':named['head']}]
                elif pid==188:args=[named['k'],named['prices']]
                else:
                    a,b=named['listA'],named['listB'];sa,sb=named['skipA'],named['skipB']
                    if named['intersectVal']:
                        if a[sa:]!=b[sb:] or not a[sa:] or a[sa]!=named['intersectVal']:raise ValueError('official shared-tail custom judge identity')
                        args=[shared(a[:sa],b[:sb],a[sa:])]
                    else:args=[shared(a,b,[])]
            rows.append(args)
        if not rows:raise ValueError('official examples missing')
        result[pid]=rows
    return result


def build_cases(definitions=None,read_raw=None):
    data={pid:[] for pid in IDS};seen={pid:set() for pid in IDS}
    def add(pid,args,category):
        key=encoded(args)
        if key in seen[pid]:return
        want=oracle.expected(pid,args);seen[pid].add(key);data[pid].append({'args':args,'expected':want,'category':category,'compare':'official-r-v1'})
    if definitions is not None:
        for pid,rows in official_inputs(definitions,read_raw).items():
            for args in rows:add(pid,args,'public-official-example-independent-result')
    alphabet=(('get',[0]),('get',[1]),('put',[0,0]),('put',[1,1]),('put',[0,2]))
    for capacity in (1,2):
        for length in range(5):
            for trace in product(alphabet,repeat=length):add(146,[['LRUCache']+[v[0] for v in trace],[[capacity]]+[list(v[1]) for v in trace]],'exhaustive-tiny-LRU-traces')
    add(146,[['LRUCache','put','put','get','get'],[[3000],[10000,100000],[0,0],[10000],[0]]],'capacity-and-key-value-maxima')
    add(146,[['LRUCache']+['get']*200000,[[3000]]+[[10000] for _ in range(200000)]],'maximum-200000-valid-method-calls')
    for n in range(1,7):
        for values in product((-1,0,1),repeat=n):add(147,[{'__list_node__':list(values)}],'all-small-list-value-orders-and-ties')
    for values in (list(range(5000)),list(reversed(range(5000))),[7]*5000,[-5000,5000]):add(147,[{'__list_node__':values}],'full-list-count-or-value-boundary')
    # Enumerate only legal nonempty-stack calls; operation count is finite.
    frontier=[(['MinStack'],[[]],0)]
    for depth in range(6):
        following=[]
        for operations,rows,size in frontier:
            add(155,[operations,rows],'exhaustive-valid-small-stack-traces')
            if depth==5:continue
            choices=[('push',[-1],size+1),('push',[1],size+1)]
            if size:choices += [('pop',[],size-1),('top',[],size),('getMin',[],size)]
            for name,row,new_size in choices:following.append((operations+[name],rows+[row],new_size))
        frontier=following
    add(155,[['MinStack','push','push','getMin','pop','getMin'],[[],[-2**31],[2**31-1],[],[],[]]],'signed32-extrema')
    add(155,[['MinStack']+['push']*30000,[[]]+[[(-2**31 if i%2 else 2**31-1)] for i in range(30000)]],'maximum-stack-calls-and-depth')
    add(155,[['MinStack','push']+['getMin']*29999,[[],[0]]+[[] for _ in range(29999)]],'maximum-stack-read-method-calls')
    for a in range(3):
        for b in range(3):
            for t in range(3):
                if a+t and b+t:add(160,[shared([1]*a,[1]*b,[1]*t)],'shared-identity-not-equal-values')
    add(160,[shared([100000]*30000,[100000]*30000,[])],'maximum-two-disjoint-equal-valued-lists')
    add(160,[shared([],[],[1]*30000)],'maximum-entire-list-shared-head')
    add(160,[shared([1]*29999,[1]*29999,[100000])],'maximum-prefixes-shared-single-tail')
    for n in range(1,5):
        shapes={}
        for ordering in permutations(range(n)):
            nodes=[]
            for value in ordering:
                if not nodes:nodes.append({'value':value,'left':None,'right':None});continue
                i=0
                while True:
                    side='left' if value<nodes[i]['value'] else 'right'
                    if nodes[i][side] is None:nodes[i][side]=len(nodes);nodes.append({'value':value,'left':None,'right':None});break
                    i=nodes[i][side]
            queue=[0];values=[]
            for i in queue:
                if i is None:values.append(None)
                else:values.append(nodes[i]['value']);queue.extend((nodes[i]['left'],nodes[i]['right']))
            while values and values[-1] is None:values.pop()
            shapes[tuple(values)]={'__tree_node__':values}
        for tree in shapes.values():
            operations=['BSTIterator'];rows=[[tree]]
            for _ in range(n):operations+=['hasNext','hasNext','next'];rows += [[],[],[]]
            operations+=['hasNext'];rows += [[]];add(173,[operations,rows],'all-small-insertion-BST-shapes-and-repeated-hasNext')
    add(173,[['BSTIterator','hasNext'],[[tree_marker(balanced(list(range(100000))))],[]]],'maximum-100000-node-balanced-constructor')
    # Right-skew compact BFS is value,null,right-value,...
    skew=[]
    for i in range(100000):skew.extend((None,i))
    skew=skew[1:]
    add(173,[['BSTIterator','hasNext'],[[{'__tree_node__':skew}],[]]],'maximum-100000-node-skew-constructor')
    add(173,[['BSTIterator']+['hasNext']*100000,[[{'__tree_node__':[1000000]}]]+[[] for _ in range(100000)]],'maximum-100000-iterator-method-calls')
    for n in range(1,7):
        for prices in product((0,1,3),repeat=n):
            for k in (1,2,3):add(188,[k,list(prices)],'exhaustive-tiny-day-action-domains')
    for prices in (list(range(1000)),list(reversed(range(1000))),[0]*1000,[0,1000]*500):
        for k in (1,100):add(188,[k,prices],'full-price-count-k-value-boundary')
    return data
