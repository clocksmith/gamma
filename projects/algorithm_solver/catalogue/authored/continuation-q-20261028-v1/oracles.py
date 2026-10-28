"""Source-blind serialized models; native identity/effects need a distinct observer."""
from collections import deque
from itertools import product
IDS=(126,129,132,133,138,140,141,142,143,144)
NATIVE=(129,133,138,141,142,143,144)
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer domain')
def word(s,lo,hi):
    if type(s) is not str or not lo<=len(s)<=hi or set(s)-set('abcdefghijklmnopqrstuvwxyz'):raise ValueError('word domain')
def validate_domain(pid,args):
    if pid not in IDS or type(args) is not list or len(args)!=(3 if pid==126 else 2 if pid==140 else 1):raise ValueError('argument envelope')
    if pid==126:
        begin,end,words=args;word(begin,1,5);word(end,len(begin),len(begin))
        if begin==end or type(words) is not list or not 1<=len(words)<=500 or len(set(words))!=len(words):raise ValueError('ladder domain')
        for w in words:word(w,len(begin),len(begin))
    if pid==132:word(args[0],1,2000)
    if pid==140:
        s,words=args;word(s,1,20)
        if type(words) is not list or not 1<=len(words)<=1000 or len(set(words))!=len(words):raise ValueError('dictionary')
        for w in words:word(w,1,10)
    if pid not in NATIVE:return
    p=args[0]
    if type(p) is not dict or type(p.get('values')) is not list:raise ValueError('indexed native packet')
    values=p['values'];n=len(values)
    bounds={129:(1,1000,0,9),133:(0,100,1,100),138:(0,1000,-10000,10000),141:(0,10000,-100000,100000),142:(0,10000,-100000,100000),143:(1,50000,1,1000),144:(0,100,-100,100)}
    minimum,maximum,lo,hi=bounds[pid]
    if not minimum<=n<=maximum:raise ValueError('native size')
    for v in values:integer(v,lo,hi)
    if pid in (129,144):
        if set(p)!={'values','left','right','root'} or len(p['left'])!=n or len(p['right'])!=n:raise ValueError('tree packet')
        if n==0:
            if p['root'] is not None:raise ValueError('empty root')
            return
        integer(p['root'],0,n-1);seen=set();stack=[(p['root'],1,0)];total=0
        while stack:
            i,depth,prefix=stack.pop()
            if i in seen:raise ValueError('tree identity repeated')
            seen.add(i)
            if pid==129 and depth>10:raise ValueError('tree depth')
            prefix=prefix*10+values[i]
            children=[p[key][i] for key in ('left','right')]
            if all(c is None for c in children):total+=prefix
            for c in children:
                if c is not None:integer(c,0,n-1);stack.append((c,depth+1,prefix))
        if len(seen)!=n:raise ValueError('disconnected tree')
        if pid==129 and total>2**31-1:raise ValueError('sum answer promise')
    if pid==133:
        if set(p)!={'values','neighbors','root'} or len(p['neighbors'])!=n or len(set(values))!=n:raise ValueError('graph packet')
        if n==0:
            if p['root'] is not None:raise ValueError('empty graph')
            return
        integer(p['root'],0,n-1)
        if values[p['root']]!=1:raise ValueError('given graph node must val1')
        for i,row in enumerate(p['neighbors']):
            if type(row) is not list or len(set(row))!=len(row):raise ValueError('neighbor list')
            for j in row:
                integer(j,0,n-1)
                if i==j or i not in p['neighbors'][j]:raise ValueError('undirected simplegraph')
        seen={p['root']};pending=[p['root']]
        for i in pending:
            for j in p['neighbors'][i]:
                if j not in seen:seen.add(j);pending.append(j)
        if len(seen)!=n:raise ValueError('connected graph')
    if pid==138:
        if set(p)!={'values','random'} or len(p['random'])!=n:raise ValueError('random list packet')
        for i in p['random']:
            if i is not None:integer(i,0,n-1)
    if pid in (141,142):
        if set(p)!={'values','pos'}:raise ValueError('cycle packet')
        integer(p['pos'],-1,n-1)
    if pid==143 and set(p)!={'values'}:raise ValueError('list packet')
def reference(pid,args):
    validate_domain(pid,args)
    if pid==126:
        begin,end,words=args
        if len(words)>15:raise ValueError('reference budget')
        if end not in words:return []
        vertices=list(dict.fromkeys([begin]+words));adj={a:[b for b in vertices if sum(x!=y for x,y in zip(a,b))==1] for a in vertices};pending=deque([[begin]]);answer=[];shortest=None
        while pending:
            path=pending.popleft()
            if shortest is not None and len(path)>shortest:break
            if path[-1]==end:answer.append(path);shortest=len(path);continue
            for nxt in adj[path[-1]]:
                if nxt not in path:pending.append(path+[nxt])
        return sorted(answer)
    if pid==132:
        s=args[0]
        if len(s)>17:raise ValueError('reference budget')
        best=len(s)-1
        for mask in range(1<<(len(s)-1)):
            start=0;parts=[]
            for i in range(len(s)-1):
                if mask>>i&1:parts.append(s[start:i+1]);start=i+1
            parts.append(s[start:])
            if all(p==p[::-1] for p in parts):best=min(best,len(parts)-1)
        return best
    if pid==140:
        s,words=args
        if len(s)>16:raise ValueError('reference budget')
        answers=[];dictionary=set(words)
        for mask in range(1<<(len(s)-1)):
            parts=[];start=0
            for i in range(len(s)-1):
                if mask>>i&1:parts.append(s[start:i+1]);start=i+1
            parts.append(s[start:])
            if all(p in dictionary for p in parts):answers.append(' '.join(parts))
        return sorted(answers)
    p=args[0];values=p['values'];n=len(values)
    if pid in (129,144):
        if n==0:return []
        def paths(i,path):
            following=path+[values[i]];children=[p[key][i] for key in ('left','right') if p[key][i] is not None]
            if not children:return [following]
            return [v for c in children for v in paths(c,following)]
        if pid==129:return sum(int(''.join(map(str,path))) for path in paths(p['root'],[]))
        output=[]
        def visit(i):
            if i is None:return
            output.append(values[i]);visit(p['left'][i]);visit(p['right'][i])
        visit(p['root']);return output
    if pid==133:return {'values':values[:],'neighbors':[row[:] for row in p['neighbors']],'root':p['root']}
    if pid==138:return {'values':values[:],'random':p['random'][:]}
    if pid in (141,142):
        seen=set();current=0 if n else None
        while current is not None and current not in seen:
            seen.add(current);current=current+1 if current+1<n else p['pos'] if p['pos']!=-1 else None
        return current is not None if pid==141 else current
    if pid==143:
        order=[];left,right=0,n-1
        while left<=right:
            order.append(left)
            if left<right:order.append(right)
            left+=1;right-=1
        return {'return':None,'original_identity_order':order,'values':[values[i] for i in order]}
