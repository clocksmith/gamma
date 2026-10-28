"""S independent source-free references and native identity/effect models.
Official entry/prototype/type guards additionally require the separate S profile.
"""
from collections import Counter,deque
from itertools import product
import re
IDS=(199,203,206,208,211,212,214,222,224,225)
CLASSES={208:'Trie',211:'WordDictionary',225:'MyStack'}
METHODS={208:{'insert':1,'search':1,'startsWith':1},211:{'addWord':1,'search':1},225:{'push':1,'pop':0,'top':0,'empty':0}}

def integer(x,l,h):return type(x) is int and l<=x<=h

def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    return a==b

def lower(s,minimum,maximum):return type(s) is str and minimum<=len(s)<=maximum and all('a'<=c<='z' for c in s)

def list_order(packet):
    n=len(packet['values']);order=[];seen=set();i=packet['head']
    while i is not None:
        if not integer(i,0,n-1) or i in seen:raise ValueError('listcycle/index')
        seen.add(i);order.append(i);i=packet['next'][i]
    if len(order)!=n:raise ValueError('listpool must be exactly reachable')
    return order

def tree_order(packet):
    n=len(packet['values']);pending=[] if packet['root'] is None else [packet['root']];seen=set()
    for i in pending:
        if not integer(i,0,n-1) or i in seen:raise ValueError('treecycle/alias/index')
        seen.add(i)
        pending.extend(c for c in (packet['left'][i],packet['right'][i]) if c is not None)
    if len(seen)!=n:raise ValueError('treepool must be exactly reachable')
    return pending

def calculator(text):
    if type(text) is not str or not 1<=len(text)<=300000 or any(c not in '0123456789+-() ' for c in text):raise ValueError('calculator alphabet/length')
    tokens=re.findall(r'[0-9]+|[()+-]',text);values=[];ops=[];want=True;last=None
    def apply():
        op=ops.pop()
        if op=='u':
            if not values:raise ValueError('missingunaryoperand')
            value=-values.pop()
        else:
            if len(values)<2:raise ValueError('missingbinaryoperand')
            b=values.pop();a=values.pop();value=a+b if op=='+' else a-b
        if not -2**31<=value<2**31:raise ValueError('runningint32')
        values.append(value)
    for token in tokens:
        if token.isdigit():
            if not want or int(token)>2**31-1:raise ValueError('numberplacement/int32')
            values.append(int(token));want=False
        elif token=='(':
            if not want:raise ValueError('implicitmultiplication')
            ops.append('(');want=True
        elif token==')':
            if want:raise ValueError('empty/trailingoperator')
            while ops and ops[-1]!='(':apply()
            if not ops:raise ValueError('unbalancedclose')
            ops.pop();want=False
        elif want:
            if token!='-' or last in ('+','-'):raise ValueError('unaryplus/consecutiveoperators')
            ops.append('u')
        else:
            while ops and ops[-1]!='(':apply()
            ops.append(token);want=True
        last=token
    if want:raise ValueError('empty/trailingoperator')
    while ops:
        if ops[-1]=='(':raise ValueError('unbalancedopen')
        apply()
    if len(values)!=1:raise ValueError('invalidexpression')
    return values[0]

def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('fixedidentity/orderedargs')
    arity=2 if pid in (203,208,211,212,225) else 1
    if len(args)!=arity:raise ValueError('arity')
    a=args[0]
    if pid in (199,222):
        limit=100 if pid==199 else 50000;lo=-100 if pid==199 else 0;hi=100 if pid==199 else 50000
        if type(a) is not dict or set(a)!={'values','left','right','root'} or type(a['values']) is not list or len(a['values'])>limit or not all(integer(v,lo,hi) for v in a['values']):raise ValueError('treevalues')
        n=len(a['values'])
        if any(type(a[k]) is not list or len(a[k])!=n or any(x is not None and not integer(x,0,n-1) for x in a[k]) for k in ('left','right')) or (a['root'] is not None and not integer(a['root'],0,n-1)):raise ValueError('treeedges')
        tree_order(a)
        if pid==222:
            pending=[a['root']];hole=False
            for i in pending:
                if i is None:hole=True;continue
                if hole:raise ValueError('notcomplete')
                pending.extend((a['left'][i],a['right'][i]))
    elif pid in (203,206):
        limit=10000 if pid==203 else 5000;lo=1 if pid==203 else -5000;hi=50 if pid==203 else 5000
        if type(a) is not dict or set(a)!={'values','next','head'} or type(a['values']) is not list or len(a['values'])>limit or not all(integer(x,lo,hi) for x in a['values']):raise ValueError('listvalues')
        n=len(a['values'])
        if type(a['next']) is not list or len(a['next'])!=n or any(i is not None and not integer(i,0,n-1) for i in a['next']) or(a['head'] is not None and not integer(a['head'],0,n-1)):raise ValueError('listedges')
        list_order(a)
        if pid==203 and not integer(args[1],0,50):raise ValueError('valdomain')
    elif pid in CLASSES:
        ops,rows=args;cap=30000 if pid==208 else 10000 if pid==211 else 100
        if type(ops) is not list or type(rows) is not list or not 1<=len(ops)<=cap+1 or len(ops)!=len(rows) or ops[0]!=CLASSES[pid] or rows[0]!=[]:raise ValueError('nativeconstructor/trace')
        size=0
        for name,row in zip(ops[1:],rows[1:]):
            if type(name) is not str or name not in METHODS[pid] or type(row) is not list or len(row)!=METHODS[pid][name]:raise ValueError('nativemethod/arity')
            if pid==225:
                if name=='push':
                    if not integer(row[0],1,9):raise ValueError('stackpush')
                    size+=1
                elif name in ('pop','top'):
                    if size==0:raise ValueError('emptyoperation')
                    size-=name=='pop'
            elif pid==208:
                if not lower(row[0],1,2000):raise ValueError('trieword')
            elif name=='addWord':
                if not lower(row[0],1,25):raise ValueError('dictionaryadd')
            elif type(row[0]) is not str or not 1<=len(row[0])<=25 or any(not('a'<=c<='z' or c=='.') for c in row[0]) or row[0].count('.')>2:raise ValueError('dictionaryquery')
    elif pid==212:
        words=args[1]
        if type(a) is not list or not 1<=len(a)<=12 or any(type(r) is not list or not 1<=len(r)<=12 or len(r)!=len(a[0]) or any(not lower(c,1,1) for c in r) for r in a):raise ValueError('boarddomain')
        if type(words) is not list or not 1<=len(words)<=30000 or any(not lower(w,1,10) for w in words) or len(set(words))!=len(words):raise ValueError('wordsdomain')
    elif pid==214:
        if not lower(a,0,50000):raise ValueError('stringdomain')
    else:calculator(a)
validate_domain=validate

def expected(pid,args):
    validate(pid,args);a=args[0]
    if pid==199:
        by_depth={};todo=[] if a['root'] is None else [(a['root'],0)]
        while todo:
            i,d=todo.pop();by_depth[d]=a['values'][i]
            # Left-first DFS overwrites by rightmost node at each depth.
            if a['right'][i] is not None:todo.append((a['right'][i],d+1))
            if a['left'][i] is not None:todo.append((a['left'][i],d+1))
        return [by_depth[i] for i in range(len(by_depth))]
    if pid in (203,206):
        order=list_order(a);order=[i for i in order if a['values'][i]!=args[1]] if pid==203 else order[::-1]
        return {'head':order[0] if order else None,'order':order,'values':[a['values'][i] for i in order]}
    if pid in CLASSES:
        out=[None];words=set();stack=[]
        for name,row in zip(a[1:],args[1][1:]):
            if pid==225:
                if name=='push':stack.append(row[0]);value=None
                elif name=='pop':value=stack.pop()
                elif name=='top':value=stack[-1]
                else:value=not stack
            elif name in ('insert','addWord'):words.add(row[0]);value=None
            elif name=='startsWith':value=any(w.startswith(row[0]) for w in words)
            elif pid==208:value=row[0] in words
            else:value=any(len(w)==len(row[0]) and all(q=='.' or q==c for q,c in zip(row[0],w)) for w in words)
            out.append(value)
        return out
    if pid==212:
        m,n=len(a),len(a[0]);counts=Counter(c for row in a for c in row);found=[];work=0
        for word in args[1]:
            if Counter(word)-counts:continue
            def search(r,c,index,used):
                nonlocal work
                work+=1
                if work>500000:raise ValueError('Independent per-word walk reference budget')
                if a[r][c]!=word[index]:return False
                if index+1==len(word):return True
                used=used|{r*n+c}
                return any(0<=rr<m and 0<=cc<n and rr*n+cc not in used and search(rr,cc,index+1,used) for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)))
            if any(search(r,c,0,frozenset()) for r in range(m) for c in range(n)):found.append(word)
        return sorted(found)
    if pid==214:
        if len(a)>500:
            if a==a[::-1]:return a
            if a[:-1]==a[-2::-1]:return a[-1]+a
            raise ValueError('Independent palindromic-prefix reference budget')
        longest=max(i for i in range(len(a)+1) if a[:i]==a[:i][::-1]);return a[longest:][::-1]+a
    if pid==222:return len(tree_order(a))
    return calculator(a)

def accepts_result(pid,args,result):
    wanted=expected(pid,args)
    if pid==212:return type(result) is list and all(type(w) is str for w in result) and len(set(result))==len(result) and sorted(result)==wanted
    return exact(result,wanted)

def effect_plan(pid,args):
    validate(pid,args)
    if pid in (199,222):
        p=args[0];before=[{'value':v,'left':p['left'][i],'right':p['right'][i]} for i,v in enumerate(p['values'])]
        return {'pool_before':before,'pool_after_exact':before,'argument_roots':[p['root']],'result_root':None,'result_order':None,'raw_args_immutable':True}
    if pid in (203,206):
        p=args[0];wanted=expected(pid,args);before=[{'value':v,'next':p['next'][i]} for i,v in enumerate(p['values'])];nexts={i:wanted['order'][j+1] if j+1<len(wanted['order']) else None for j,i in enumerate(wanted['order'])}
        return {'pool_before':before,'all_original_values':[r['value'] for r in before],'required_next':nexts,'unconstrained_next_ids':[] if pid==206 else [i for i in range(len(before)) if i not in nexts],'argument_roots':[p['head']],'result_root':wanted['head'],'result_order':wanted['order'],'raw_args_immutable':True}
    return {'raw_args_immutable':True,'native_receiver_count':1 if pid in CLASSES else None}

def check_effects(pid,args,record):
    if not exact(record.get('args_before'),args) or not exact(record.get('args_after'),args):return False,'input_effect'
    if pid not in (199,203,206,222):return True,None
    plan=effect_plan(pid,args);identity=record.get('node_identity')
    if type(identity) is not dict or not exact(identity.get('before'),plan['pool_before']) or not exact(identity.get('argument_roots'),plan['argument_roots']) or not exact(identity.get('result_root'),plan['result_root']) or not exact(identity.get('result_order'),plan['result_order']):return False,'node_identity'
    after=identity.get('after')
    if pid in (199,222):
        if not exact(after,plan['pool_after_exact']):return False,'tree_effect'
    else:
        if type(after) is not list or len(after)!=len(plan['pool_before']):return False,'list_pool'
        for i,row in enumerate(after):
            if type(row) is not dict or set(row)!={'value','next'} or not exact(row['value'],plan['all_original_values'][i]):return False,'list_value_effect'
            if i in plan['required_next'] and not exact(row['next'],plan['required_next'][i]):return False,'list_link_effect'
    return True,None

def check_observation(pid,args,record,language):
    """Semantic/effect check only; official source/runtime guards require host_check."""
    if not accepts_result(pid,args,record.get('result')):return False,'wrong_answer'
    return check_effects(pid,args,record)
