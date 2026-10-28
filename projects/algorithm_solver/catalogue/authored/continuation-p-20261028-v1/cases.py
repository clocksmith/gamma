"""Bounded P source-blind cases; official bodies remain operator-private."""
import ast
import hashlib
import html
import importlib.util
from itertools import combinations,product
import json
from pathlib import Path
import random
import re

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('continuation_p_independent_oracles',HERE/'oracles.py')
oracle=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(oracle)
IDS=oracle.IDS
SEED=2026102816


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def official_inputs(directory,read_raw=None):
    specs=json.loads((HERE/'contracts.json').read_bytes())['problems'];result={}
    for spec in specs:
        pid=spec['id'];path=Path(directory)/f'{pid}.json';raw=path.read_bytes() if read_raw is None else read_raw(pid,path)
        q=json.loads(raw)['data']['question']
        if (hashlib.sha256(raw).hexdigest()!=spec['definition']['response_sha256'] or q['questionFrontendId']!=str(pid) or q['titleSlug']!=spec['definition']['slug'] or q['isPaidOnly'] is not False or hashlib.sha256(q['content'].encode()).hexdigest()!=spec['definition']['content_sha256']):raise ValueError('exact public spec drift')
        text=html.unescape(re.sub('<[^>]*>',' ',q['content']))
        values=[]
        for match in re.finditer(r'Input:\s*(.*?)\s*Output:',text,re.S):
            source=re.sub(r'\bnull\b','None',match[1].strip())
            call=ast.parse('f('+source+')',mode='eval').body
            if not isinstance(call,ast.Call) or call.args or [k.arg for k in call.keywords]!=spec['argument_order']:raise ValueError('official example argument grammar')
            args=[ast.literal_eval(k.value) for k in call.keywords]
            if pid in (99,114,116,117):args[0]={'__next_node__' if pid in (116,117) else '__tree_node__':args[0]}
            values.append(args)
        if not values:raise ValueError('official examples missing')
        result[pid]=values
    return result


def balanced(values):
    if not values:return None
    mid=len(values)//2
    return values[mid],balanced(values[:mid]),balanced(values[mid+1:])


def chain(n,right=True,next_node=False):
    nodes=[{'value':i if n>2000 else (i%201)-100,'left':None,'right':None} for i in range(n)]
    for i in range(n-1):nodes[i]['right' if right else 'left']=i+1
    return oracle.marker(nodes,next_node=next_node)


def build_cases(definitions=None,read_raw=None):
    data={pid:[] for pid in IDS};seen={pid:set() for pid in IDS};rng=random.Random(SEED)
    def add(pid,args,category):
        key=encoded(args)
        if key in seen[pid]:return
        want=oracle.expected(pid,args);seen[pid].add(key)
        data[pid].append({'args':args,'expected':want,'category':category,'compare':'official-p-v1'})
    if definitions is not None:
        for pid,rows in official_inputs(definitions,read_raw).items():
            for args in rows:add(pid,args,'official-public-example-independent-expectation')
    for n in range(1,4):
        for digits in product('23456789',repeat=n):add(17,[''.join(digits)],'exhaustive-phone-length1-to3')
    for d in '23456789':add(17,[d*4],'maximum-phone-length')
    for _ in range(128):add(17,[''.join(rng.choices('23456789',k=4))],'seeded-phone-length4')
    # A mathematical Latin-pattern Sudoku; one missing cell per row/column
    # intersection is uniquely forced. Full puzzle examples use exact cover.
    solved=[[str(1+(3*r+r//3+c)%9) for c in range(9)] for r in range(9)]
    add(37,[[list(row) for row in solved]],'complete-lawful-unique-board')
    for r,c in [(0,0),(0,8),(8,0),(8,8),(4,4)]+[(i,i) for i in range(1,8)]:
        board=[list(row) for row in solved];board[r][c]='.';add(37,[board],'uniquely-forced-single-hole')
    for digit_shift in range(1,9):
        board=[[str(1+(int(d)-1+digit_shift)%9) for d in row] for row in solved]
        for c in range(9):board[0][c]='.'
        add(37,[board],'unique-first-row-digit-permutation')
    alphabet='01+-.eEa'
    for n in range(1,5):
        for chars in product(alphabet,repeat=n):add(65,[''.join(chars)],'exhaustive-number-grammar-small')
    for s in ('9'*20,'a'*20,'12345678901234567890','+'+'0'*19,'-'+'0'*19,'1e'+'9'*18,'.'+'0'*19,'0'*19+'.','0e'+'+'+'0'*17,'NaN','Infinity','1E-10','1e+','E1'):
        add(65,[s],'numeric-full-length-and-lexical-boundary')
    for _ in range(128):add(65,[''.join(rng.choices('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-.',k=rng.randint(5,20)))],'seeded-lawful-ascii-domain')
    for n in range(1,5):
        words=[''.join(t) for t in product('ab',repeat=n)]
        for a,b in product(words,repeat=2):add(87,[a,b],'exhaustive-binary-scramble-pairs')
    for _ in range(64):
        n=rng.randint(5,7);add(87,[''.join(rng.choices('abc',k=n)),''.join(rng.choices('abc',k=n))],'seeded-small-scramble')
    for a,b in [('a'*30,'a'*30),('a'*30,'a'*29+'b'),('abcdefghijklmnoabcdefghijklmno','onmlkjihgfedcbaonmlkjihgfedcba'),('a'*15+'b'*15,'b'*15+'a'*15)]:add(87,[a,b],'maximum-string-length-witness')
    for n in range(1,9):add(95,[n],'complete-Catalan-forest-all-allowed-n')
    for n in range(2,6):
        for shape in oracle.shapes(n):
            tree=oracle.tuple_marker(oracle.labelled(shape)[0]);nodes=oracle.tree_nodes(tree)
            for i,j in combinations(range(n),2):
                swapped=[dict(row) for row in nodes];swapped[i]['value'],swapped[j]['value']=swapped[j]['value'],swapped[i]['value']
                add(99,[oracle.marker(swapped)],'all-small-BST-shapes-and-two-value-swaps')
    for right in (False,True):
        nodes=[{'value':i,'left':None,'right':None} for i in range(1000)]
        # Monotonic inorder values for either original spine.
        for i in range(999):nodes[i]['right' if right else 'left']=i+1
        for i,row in enumerate(nodes):row['value']=i if right else 999-i
        nodes[0]['value'],nodes[-1]['value']=nodes[-1]['value'],nodes[0]['value']
        add(99,[oracle.marker(nodes)],'maximum-1000-node-skew-exact-swap')
    add(99,[{'__tree_node__':[-2**31,2**31-1]}],'signed32-extreme-swapped-values')
    for n in range(1,9):
        for nums in combinations(range(-4,5),n):add(108,[list(nums)],'exhaustive-small-strict-sorted-subsets')
    add(108,[list(range(-5000,5000))],'maximum-10000-sorted-input')
    add(108,[[-10000,10000]],'numeric-array-extremes')
    for n in range(6):
        for shape in oracle.shapes(n):add(114,[oracle.tuple_marker(oracle.labelled(shape)[0])],'all-small-tree-shapes')
    for right in (False,True):add(114,[chain(2000,right)],'maximum-2000-node-skew')
    add(114,[oracle.tuple_marker(balanced([0]*2000))],'maximum-repeated-values-balanced')
    for depth in range(13):
        n=2**depth-1
        add(116,[{'__next_node__':[(-1000 if i%2 else 1000) for i in range(n)]}],'perfect-all-allowed-depths')
    for n in range(6):
        for shape in oracle.shapes(n):
            tree=oracle.tuple_marker(oracle.labelled(shape)[0]);add(117,[{'__next_node__':tree['__tree_node__']}],'all-small-next-tree-shapes')
    for right in (False,True):
        tree=chain(6000,right,True);tree['__next_node__']=[(v%201)-100 if v is not None else None for v in tree['__next_node__']]
        add(117,[tree],'maximum-6000-node-skew')
    tree=oracle.tuple_marker(balanced([0]*6000));add(117,[{'__next_node__':tree['__tree_node__']}],'maximum-next-balanced-repeated-values')
    return data
