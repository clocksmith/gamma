"""Focused exposed-development checks for these original sources, not qualification.

References/expected outputs stay on the host. Only argument packets, an observation
adapter and one candidate enter the existing network-isolated Linux sandbox.
Run from Gamma root on the provisioned Linux host: python3 PATH/development_checks.py
--repo-root REPO --output NEW_PRIVATE_OUTPUT. No corpus, model, hidden case or catalogue
is opened. Each source read is authorized through the existing six-anchor gate.
"""
import argparse
from collections import Counter, deque
from functools import lru_cache
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import sys

TREES={404,437,450,501,508,513,515,530,538,543,563}
MUTATING={450,538}
UNORDERED={336,501,508}


def tree(values):
    if not values:
        return None
    nodes=[None if v is None else {'val':v,'left':None,'right':None} for v in values]
    for i,node in enumerate(nodes):
        if node is not None:
            if 2*i+1<len(nodes):node['left']=nodes[2*i+1]
            if 2*i+2<len(nodes):node['right']=nodes[2*i+2]
    return nodes[0]


def bst(values):
    root=None
    for v in values:
        if root is None:root={'val':v,'left':None,'right':None};continue
        n=root
        while True:
            side='left' if v<n['val'] else 'right'
            if n[side] is None:n[side]={'val':v,'left':None,'right':None};break
            n=n[side]
    return root


def flatten(root):
    if root is None:return []
    nodes=[root];result=[]
    for n in nodes:
        row=[n['val'],None,None]
        for i,side in ((1,'left'),(2,'right')):
            if n[side] is not None:row[i]=len(nodes);nodes.append(n[side])
        result.append(row)
    return result


def visits(root):
    return [] if root is None else [root]+visits(root['left'])+visits(root['right'])


def subsequences(s):
    return {''.join(s[i] for i in range(len(s)) if mask>>i&1) for mask in range(1<<len(s))}


def reference(pid,args):
    if pid==306:
        s=args[0]
        def follow(parts,pos):
            if pos==len(s):return len(parts)>=3
            for end in range(pos+1,len(s)+1):
                word=s[pos:end]
                if len(word)>1 and word[0]=='0':break
                v=int(word)
                if len(parts)>=2 and v!=parts[-1]+parts[-2]:continue
                if follow(parts+[v],end):return True
            return False
        return follow([],0)
    if pid==312:
        @lru_cache(None)
        def burst(a):
            return max(((a[i-1] if i else 1)*a[i]*(a[i+1] if i+1<len(a) else 1)+burst(a[:i]+a[i+1:]) for i in range(len(a))),default=0)
        return burst(tuple(args[0]))
    if pid==315:return [sum(v<x for v in args[0][i+1:]) for i,x in enumerate(args[0])]
    if pid==327:
        nums,low,high=args
        return sum(low<=sum(nums[i:j])<=high for i in range(len(nums)) for j in range(i+1,len(nums)+1))
    if pid==329:
        a=args[0];m,n=len(a),len(a[0])
        def walk(r,c):return 1+max((walk(rr,cc) for rr,cc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)) if 0<=rr<m and 0<=cc<n and a[rr][cc]>a[r][c]),default=0)
        return max(walk(r,c) for r in range(m) for c in range(n))
    if pid==330:
        nums,n=args;target=(1<<(n+1))-1;start=1
        for v in nums:start=(start|(start<<v))&target
        queue=deque([(start,0)]);seen={start}
        while queue:
            mask,cost=queue.popleft()
            if mask==target:return cost
            for v in range(1,n+1):
                nxt=(mask|(mask<<v))&target
                if nxt not in seen:seen.add(nxt);queue.append((nxt,cost+1))
    if pid==335:
        x=y=0;segments=[]
        for i,length in enumerate(args[0]):
            dx,dy=((0,1),(-1,0),(0,-1),(1,0))[i%4];xx,yy=x+dx*length,y+dy*length
            box=(min(x,xx),max(x,xx),min(y,yy),max(y,yy))
            for a,b,c,d in segments[:-1]:
                if max(a,box[0])<=min(b,box[1]) and max(c,box[2])<=min(d,box[3]):return True
            segments.append(box);x,y=xx,yy
        return False
    if pid==336:
        a=args[0]
        return [[i,j] for i in range(len(a)) for j in range(len(a)) if i!=j and a[i]+a[j]==(a[i]+a[j])[::-1]]
    if pid==354:
        a=args[0]
        def walk(i):return 1+max((walk(j) for j in range(len(a)) if a[j][0]>a[i][0] and a[j][1]>a[i][1]),default=0)
        return max(walk(i) for i in range(len(a)))
    if pid==363:
        a,k=args;m,n=len(a),len(a[0]);possible=[]
        for r in range(m):
            for rr in range(r+1,m+1):
                for c in range(n):
                    for cc in range(c+1,n+1):
                        v=sum(a[i][j] for i in range(r,rr) for j in range(c,cc))
                        if v<=k:possible.append(v)
        if not possible:raise ValueError('generated matrix lacks the promised rectangle')
        return max(possible)
    if pid==391:
        cells=Counter((x,y) for a,b,c,d in args[0] for x in range(a,c) for y in range(b,d))
        return len(cells)==(max(x for x,y in cells)-min(x for x,y in cells)+1)*(max(y for x,y in cells)-min(y for x,y in cells)+1) and all(v==1 for v in cells.values())
    if pid==399:
        eq,values,queries=args;nodes=set(x for pair in eq for x in pair);ratios={(x,x):1.0 for x in nodes}
        for (a,b),v in zip(eq,values):ratios[a,b]=v;ratios[b,a]=1/v
        for k in nodes:
            for a in nodes:
                for b in nodes:
                    if (a,k) in ratios and (k,b) in ratios:ratios[a,b]=ratios[a,k]*ratios[k,b]
        return [ratios.get(tuple(q),-1.0) for q in queries]
    if pid==407:
        a=args[0];m,n=len(a),len(a[0]);thresholds=sorted({v for row in a for v in row});answer=0
        for r in range(1,m-1):
            for c in range(1,n-1):
                for level in thresholds:
                    if level<a[r][c]:continue
                    queue=[(r,c)];seen={(r,c)};escaped=False
                    for x,y in queue:
                        if x in (0,m-1) or y in (0,n-1):escaped=True;break
                        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                            if 0<=xx<m and 0<=yy<n and (xx,yy) not in seen and a[xx][yy]<=level:seen.add((xx,yy));queue.append((xx,yy))
                    if escaped:answer+=level-a[r][c];break
        return answer
    if pid in TREES:
        root=args[0];nodes=visits(root)
        def subtotal(n):return 0 if n is None else n['val']+subtotal(n['left'])+subtotal(n['right'])
        if pid==404:return sum(n['left']['val'] for n in nodes if n['left'] is not None and n['left']['left'] is None and n['left']['right'] is None)
        if pid==437:
            def paths(n,total):return 0 if n is None else int(total+n['val']==args[1])+paths(n['left'],total+n['val'])+paths(n['right'],total+n['val'])
            return sum(paths(n,0) for n in nodes)
        if pid==450:return sorted(n['val'] for n in nodes if n['val']!=args[1])
        if pid==501:
            counts=Counter(n['val'] for n in nodes);maximum=max(counts.values());return [v for v,c in counts.items() if c==maximum]
        if pid==508:
            counts=Counter(subtotal(n) for n in nodes);maximum=max(counts.values());return [v for v,c in counts.items() if c==maximum]
        if pid in (513,515):
            levels={}
            def walk(n,d):
                if n is not None:levels.setdefault(d,[]).append(n['val']);walk(n['left'],d+1);walk(n['right'],d+1)
            walk(root,0)
            return levels[max(levels)][0] if pid==513 else [max(levels[d]) for d in sorted(levels)]
        if pid==530:return min(abs(a['val']-b['val']) for i,a in enumerate(nodes) for b in nodes[i+1:])
        if pid==538:
            sums={n['val']:sum(m['val'] for m in nodes if m['val']>=n['val']) for n in nodes}
            def updated(n):return None if n is None else {'val':sums[n['val']],'left':updated(n['left']),'right':updated(n['right'])}
            return flatten(updated(root))
        if pid==543:
            graph={id(n):[] for n in nodes}
            for n in nodes:
                for c in (n['left'],n['right']):
                    if c is not None:graph[id(n)].append(id(c));graph[id(c)].append(id(n))
            best=0
            for n in graph:
                q=[(n,-1,0)]
                for v,p,d in q:
                    best=max(best,d);q.extend((c,v,d+1) for c in graph[v] if c!=p)
            return best
        if pid==563:return sum(abs(subtotal(n['left'])-subtotal(n['right'])) for n in nodes)
    if pid==514:
        ring,key=args;q=deque([(0,0,0)]);seen={(0,0)}
        while q:
            position,index,cost=q.popleft()
            if index==len(key):return cost
            nxt=[((position+1)%len(ring),index),((position-1)%len(ring),index)]
            if ring[position]==key[index]:nxt.append((position,index+1))
            for p,i in nxt:
                if (p,i) not in seen:seen.add((p,i));q.append((p,i,cost+1))
    if pid==517:
        a=tuple(args[0]);n=len(a)
        if sum(a)%n:return -1
        goal=(sum(a)//n,)*n;q=deque([(a,0)]);seen={a}
        while q:
            state,cost=q.popleft()
            if state==goal:return cost
            options=[[None]+([i-1] if i and state[i] else [])+([i+1] if i+1<n and state[i] else []) for i in range(n)]
            for destinations in itertools.product(*options):
                nxt=list(state)
                for i,d in enumerate(destinations):
                    if d is not None:nxt[i]-=1;nxt[d]+=1
                nxt=tuple(nxt)
                if nxt not in seen:seen.add(nxt);q.append((nxt,cost+1))
    if pid==518:
        amount,coins=args
        def ways(i,left):return int(left==0) if i==len(coins) else sum(ways(i+1,left-c*coins[i]) for c in range(left//coins[i]+1))
        return ways(0,amount)
    if pid==521:return max((len(s) for s in subsequences(args[0])^subsequences(args[1])),default=-1)
    if pid==522:
        counts=Counter(s for word in args[0] for s in subsequences(word));return max((len(s) for s,count in counts.items() if count==1),default=-1)
    if pid==523:
        a,k=args;return any(sum(a[i:j])%k==0 for i in range(len(a)) for j in range(i+2,len(a)+1))
    if pid==524:
        s,words=args;valid=subsequences(s);return min((w for w in words if w in valid),key=lambda w:(-len(w),w),default='')
    if pid==525:
        a=args[0];return max((j-i for i in range(len(a)) for j in range(i+1,len(a)+1) if sum(a[i:j])*2==j-i),default=0)
    raise ValueError(pid)


def case_packets():
    rng=random.Random(20261028);cases={}
    specs={int(r['problem_id'].split(':')[1]):r for r in json.loads((Path(__file__).parent/'manifest.json').read_text())['problems']}
    for pid in specs:
        rows=[]
        for i in range(16):
            a=[rng.randrange(-4,5) for _ in range(rng.randrange(1,9))]
            if pid==306:args=[''.join(rng.choice('0123') for _ in range(rng.randrange(1,9)))];
            elif pid==312:args=[[rng.randrange(0,5) for _ in range(rng.randrange(1,7))]]
            elif pid==315:args=[a]
            elif pid==327:
                lo=rng.randrange(-6,4);args=[a,lo,rng.randrange(lo,7)]
            elif pid==329:args=[[[rng.randrange(5) for _ in range(3)] for _ in range(3)]]
            elif pid==330:args=[sorted(rng.randrange(1,8) for _ in range(rng.randrange(1,5))),rng.randrange(1,11)]
            elif pid==335:args=[[rng.randrange(1,5) for _ in range(rng.randrange(1,12))]]
            elif pid==336:
                pool=[''.join(chars) for n in range(4) for chars in itertools.product('ab',repeat=n)];args=[rng.sample(pool,rng.randrange(1,9))]
            elif pid==354:args=[[[rng.randrange(1,6),rng.randrange(1,6)] for _ in range(6)]]
            elif pid==363:args=[[[rng.randrange(-3,4) for _ in range(4)] for _ in range(3)],rng.randrange(0,6)]
            elif pid==391:
                rect=[]
                for _ in range(4):
                    x,y=rng.randrange(-2,2),rng.randrange(-2,2);rect.append([x,y,x+rng.randrange(1,3),y+rng.randrange(1,3)])
                args=[rect]
            elif pid==399:
                p=[rng.randrange(1,9) for _ in range(5)];args=[[['a','b'],['b','c'],['x','y']],[p[0]/p[1],p[1]/p[2],p[3]/p[4]],[['a','c'],['c','a'],['a','a'],['a','x'],['z','z']]]
            elif pid==407:args=[[[rng.randrange(0,6) for _ in range(4)] for _ in range(4)]]
            elif pid in TREES:
                root=bst(rng.sample(range(-20,21),rng.randrange(2,10))) if pid in (450,501,530,538) else tree(a)
                if pid==530:root=bst(rng.sample(range(21),rng.randrange(2,10)))
                args=[root]+([rng.randrange(-5,6)] if pid in (437,450) else [])
            elif pid==514:
                ring=''.join(rng.choice('abc') for _ in range(6));args=[ring,''.join(rng.choice(ring) for _ in range(4))]
            elif pid==517:args=[[rng.randrange(3) for _ in range(rng.randrange(2,5))]]
            elif pid==518:args=[rng.randrange(11),rng.sample(range(1,7),rng.randrange(1,5))]
            elif pid==521:args=[''.join(rng.choice('ab') for _ in range(rng.randrange(1,7))) for _ in range(2)]
            elif pid==522:args=[[''.join(rng.choice('ab') for _ in range(rng.randrange(1,6))) for _ in range(rng.randrange(2,6))]]
            elif pid==523:args=[[abs(v) for v in a],rng.randrange(1,10)]
            elif pid==524:args=[''.join(rng.choice('abc') for _ in range(8)),[''.join(rng.choice('abc') for _ in range(rng.randrange(1,6))) for _ in range(7)]]
            elif pid==525:args=[[rng.randrange(2) for _ in range(10)]]
            else:raise ValueError(pid)
            try:reference(pid,args)
            except ValueError:continue
            rows.append(args)
        cases[pid]=rows
    extras={
        306:[['112358'],['199100199'],['000'],['1023'],['0123'],['101'],['1']],
        312:[[[3,1,5,8]],[[0]],[[1,5]]],
        315:[[[5,2,6,1]],[[2,2,2]]],
        327:[[[-2,5,-1],-2,2],[[0,0,0],0,0],[[2147483647,-2147483648,-1],-1,0]],
        329:[[[[9,9,4],[6,6,8],[2,1,1]]],[[[0]]]],
        330:[[[1,3],6],[[1,5,10],20]],
        335:[[[2,1,1,2]],[[1,2,3,4]],[[1,1,1,1]],[[1,1,2,1,1]],[[2,1,1,3,1,1]]],
        336:[[['abcd','dcba','lls','s','sssll']],[['a','']],[['bat','tab','cat']]],
        354:[[[[5,4],[6,4],[6,7],[2,3]]]],
        363:[[[[1,0,1],[0,-2,3]],2],[[[-5]],-2]],
        391:[[[[1,1,3,3],[3,1,4,2],[3,2,4,4],[1,3,2,4],[2,3,3,4]]]],
        407:[[[[1,4,3,1,3,2],[3,2,1,3,2,4],[2,3,3,2,3,1]]]],
        437:[[tree([10,5,-3,3,2,None,11,3,-2,None,1]),8],[tree([0,0,0]),0],[None,0]],
        501:[[bst([1,2,2])]],513:[[tree([2,1,3])]],514:[['godding','gd']],515:[[None]],
        517:[[[1,0,5]],[[0,3,0]],[[0,2,0]]],518:[[5,[1,2,5]],[0,[1]]],
        521:[['aaa','aaa'],['aba','cdc']],522:[[['aaa','aaa','aa']],[['aba','cdc','eae']]],
        523:[[[23,2,4,6,7],6],[[0,0],7],[[1,0],2]],
        524:[['abpcplea',['ale','apple','monkey','plea']]],525:[[[0,1]],[[0,1,0]]],
        530:[[bst([0,100000])]],538:[[None]],543:[[tree([1,2,3,4,5])]],563:[[None],[tree([1,2,3])]]
    }
    for pid,rows in extras.items():
        cases[pid].extend(rows)
    return specs,cases


PY_HARNESS=r'''
import json,importlib.util
spec=importlib.util.spec_from_file_location('candidate','/task/candidate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val,self.left,self.right=val,left,right

def build(n):return None if n is None else TreeNode(n['val'],build(n['left']),build(n['right']))
def flat(root):
    if root is None:return []
    nodes=[root];seen={id(root):0};out=[]
    for n in nodes:
        row=[n.val,None,None]
        for i,c in ((1,n.left),(2,n.right)):
            if c is not None:
                if id(c) in seen:raise ValueError('cycle or shared tree node')
                seen[id(c)]=len(nodes);row[i]=len(nodes);nodes.append(c)
        out.append(row)
    return out
packet=json.load(open('/task/arguments.json'));pid=packet['id'];fn=getattr(module.Solution(),packet['method'])
for data in packet['cases']:
    args=data.copy()
    if packet['tree']:args[0]=build(args[0])
    original=args[0] if packet['tree'] else None
    result=fn(*args)
    after=[flat(args[0])]+args[1:] if packet['tree'] else args
    print(json.dumps({'result':flat(result) if pid in (450,538) else result,'after':after,'root_identity':result is original if pid==538 else None},allow_nan=False))
'''
JS_HARNESS=r'''
const fs=require('node:fs'),moduleValue=require('/task/candidate.cjs'),packet=JSON.parse(fs.readFileSync('/task/arguments.json','utf8'));
class TreeNode{constructor(val=0,left=null,right=null){this.val=val;this.left=left;this.right=right;}}
const build=n=>n===null?null:new TreeNode(n.val,build(n.left),build(n.right));
function flat(root){if(!root)return [];const nodes=[root],seen=new Set([root]),out=[];for(const n of nodes){const row=[n.val,null,null];for(const [i,c] of [[1,n.left],[2,n.right]])if(c){if(seen.has(c))throw Error('cycle or shared tree node');seen.add(c);row[i]=nodes.length;nodes.push(c);}out.push(row);}return out;}
if(moduleValue[packet.method]!==moduleValue.solve)throw Error('missing native method export');
for(const data of packet.cases){const args=structuredClone(data);if(packet.tree)args[0]=build(args[0]);const original=packet.tree?args[0]:null,result=moduleValue[packet.method](...args);console.log(JSON.stringify({result:[450,538].includes(packet.id)?flat(result):result,after:packet.tree?[flat(args[0]),...args.slice(1)]:args,root_identity:packet.id===538?result===original:null}));}
'''


def equal(pid,actual,expected):
    if pid in UNORDERED:return sorted(actual)==sorted(expected)
    if pid==399:return len(actual)==len(expected) and all(math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9) for a,b in zip(actual,expected))
    if pid==450:
        values=[];stack=[(0,-math.inf,math.inf)] if actual else [];seen=set()
        while stack:
            i,lo,hi=stack.pop()
            if not isinstance(i,int) or not 0<=i<len(actual) or i in seen:return False
            seen.add(i);v,left,right=actual[i]
            if not lo<v<hi:return False
            values.append(v)
            if left is not None:stack.append((left,lo,v))
            if right is not None:stack.append((right,v,hi))
        return len(seen)==len(actual) and sorted(values)==expected
    return actual==expected and (type(actual) is bool if type(expected) is bool else True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repo-root',required=True);parser.add_argument('--output',required=True);parser.add_argument('--gate',required=True);parser.add_argument('--gate-sha256',required=True);options=parser.parse_args()
    root=Path(options.repo_root).resolve();sys.path.insert(0,str(root/'projects/algorithm_solver'))
    from algsolve.judge import sandbox
    from catalogue.boundary_policy import authorize_before_open
    sandbox.check_available();graw=Path(options.gate).read_bytes()
    if hashlib.sha256(graw).hexdigest()!=options.gate_sha256:raise ValueError('gate descriptor changed')
    gate=json.loads(graw);out=Path(options.output);out.mkdir(exist_ok=False,parents=True)
    specs,cases=case_packets();receipts=[];failures=[]
    for pid,spec in specs.items():
        expected=[reference(pid,a) for a in cases[pid]]
        for language in ('python','javascript'):
            authorize_before_open(f'leetcode:{pid}',gate['artifact_paths'],gate['trusted_hashes'],language=language,payload_kind='source')
            source=Path(__file__).parent/spec['sources'][language]['path'];raw=source.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=spec['sources'][language]['sha256']:raise ValueError('source hash changed')
            arguments=json.dumps({'id':pid,'method':spec['entrypoint'],'tree':pid in TREES,'cases':cases[pid]})
            if language=='python':argv=['/usr/bin/python3','-I','-S','harness.py'];files={'candidate.py':raw,'harness.py':PY_HARNESS,'arguments.json':arguments}
            else:argv=['/usr/bin/node','--jitless','--single-threaded','--max-old-space-size=256','harness.cjs'];files={'candidate.cjs':raw,'harness.cjs':JS_HARNESS,'arguments.json':arguments}
            result=sandbox.run(argv,files=files,limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=1024**3,max_output_bytes=16*1024**2))
            name=f'{pid}-{language}';(out/(name+'.stdout')).write_bytes(result.stdout);(out/(name+'.stderr')).write_bytes(result.stderr)
            rows=[]
            try:rows=[json.loads(line) for line in result.stdout.splitlines()]
            except ValueError:pass
            good=result.ok and len(rows)==len(expected);failed=[]
            for i,(row,want) in enumerate(zip(rows,expected)):
                args=cases[pid][i];unchanged=[flatten(args[0])]+args[1:] if pid in TREES else args
                valid=equal(pid,row['result'],want)
                if pid not in MUTATING:valid=valid and row['after']==unchanged
                if pid==538:valid=valid and row['root_identity'] is True and row['after'][0]==want
                if not valid:good=False;failed.append({'case':i,'args':args,'actual':row,'expected':want})
            if not good:failures.append(name)
            receipt={'id':pid,'language':language,'source_sha256':hashlib.sha256(raw).hexdigest(),'cases':len(expected),'observed_rows':len(rows),'passed':good,'exit':result.exit_code,'timed_out':result.timed_out,'wall_seconds':result.wall_seconds,'failures':failed,'stderr_tail':result.stderr.decode(errors='replace')[-500:]}
            receipts.append(receipt);print(json.dumps({k:receipt[k] for k in ('id','language','cases','observed_rows','passed')}),flush=True)
    summary={'scope':'Exposed small-case development checks; not independent qualification, full-domain coverage, official judge acceptance or catalogue admission.','problems':len(specs),'programs':len(receipts),'observed_calls':sum(r['observed_rows'] for r in receipts),'all_passed':not failures,'failures':failures,'receipts':receipts}
    (out/'development-results.json').write_text(json.dumps(summary,indent=2)+'\n')
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
