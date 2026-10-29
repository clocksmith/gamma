"""Independent bounded references and explicit maximum-domain constructions."""
import importlib.util
from pathlib import Path
import itertools
import random
from collections import deque
_spec=importlib.util.spec_from_file_location('gamma_requested589_case_oracles',Path(__file__).with_name('oracles.py'));_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain


def chain(n,value=1,right=False):
    out=[value]
    for _ in range(n-1):out.extend([None,value] if right else [value,None])
    while out and out[-1] is None:out.pop()
    return out


def bst(xs):
    nodes=[]
    def make(values):
        if not values:return None
        m=len(values)//2;i=len(nodes);nodes.append([values[m],None,None]);nodes[i][1]=make(values[:m]);nodes[i][2]=make(values[m+1:]);return i
    return _o.serialized(nodes,make(list(xs)))


def matrix_power(matrix,n):
    def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(2))%_o.MOD for j in range(2)] for i in range(2)]
    out=[[1,0],[0,1]]
    while n:
        if n&1:out=mul(out,matrix)
        matrix=mul(matrix,matrix);n//=2
    return out


def maximum(pid):
    if pid in (589,590):
        r={'values':list(range(10000)),'children':[[i+1] if i<998 else list(range(999,10000)) if i==998 else [] for i in range(10000)]}
        return [([r],list(range(10000)) if pid==589 else list(range(999,10000))+list(range(998,-1,-1)),'10000 nodes at height1000'),([{'values':[10000],'children':[[]]}],[10000],'maximum node value')]
    if pid==600:return [([10**9],reference(pid,[10**9]),'independent enumeration of admissible binary strings')]
    if pid==606:return [([chain(10000,-1000)],'-1000('*9999+'-1000'+')'*9999,'10000-node skew; literal parentheses')]
    if pid==617:return [([[10000]*2000,[10000]*2000],[20000]*2000,'2000 nodes in each input, equal values')]
    if pid==622:return [([['MyCircularQueue']+['enQueue','Rear','deQueue']*1000,[[1000]]+[[1000],[],[]]*1000],[None]+[True,1000,True]*1000,'3000 calls at capacity/value boundary')]
    if pid==623:
        original=chain(10000,100);nodes=_o.tree(original);leaf=len(nodes)-1;nodes[leaf][1]=len(nodes);nodes.append([100000,None,None]);nodes[leaf][2]=len(nodes);nodes.append([100000,None,None])
        return [([original,100000,10001],_o.serialized(nodes),'row beneath depth10000 chain; explicit node-table construction retains absent sibling nulls')]
    if pid==629:return [([1000,1000],reference(pid,[1000,1000]),'Euler pentagonal generating-product coefficient'),([1000,0],1,'unique zero-inversion permutation')]
    if pid==630:return [([[[10000,10000]]*10000],1,'one maximum-duration course fits'),([[[1,10000]]*10000],10000,'all maximum-count unit courses fit')]
    if pid==632:return [([[[i-1750]*50 for i in range(3500)]],[-1750,1749],'3500 length50 constant lists force both extrema'),([[[-100000],[100000]]],[-100000,100000],'maximum value spread')]
    if pid==637:return [([[2**31-1]*10000],[float(2**31-1)]*14,'14 levels with constant maximum node value')]
    if pid==639:
        a=matrix_power([[9,15],[1,0]],99999);b=matrix_power([[1,1],[1,0]],100000)
        return [(['*'*100000],(9*a[0][0]+a[0][1])%_o.MOD,'independent matrix exponentiation'),(['1'*100000],b[0][0],'Fibonacci matrix identity'),(['0'+'1'*99999],0,'leading zero blocks every decoding')]
    if pid==641:return [([['MyCircularDeque']+['insertFront','getRear','deleteLast','isEmpty']*500,[[1000]]+[[1000],[],[],[]]*500],[None]+[True,1000,True,True]*500,'2000 calls at maximum capacity and value')]
    if pid==652:
        a=[[200]*5000];return [(a,reference(pid,a),'literal subtree shape census on complete5000-node tree')]
    if pid==653:return [([bst(range(-5000,5000)),100000],False,'10000 bounded nodes cannot reach target')]
    if pid==654:return [([list(range(1000))],_o.serialized([[v,i+1 if i<999 else None,None] for i,v in enumerate(range(999,-1,-1))]),'1000 increasing inputs force a descending left chain')]
    if pid==655:
        a=[[-99]*1023];return [(a,reference(pid,a),'depth10 allows1023 nodes;1024 is not jointly feasible with this depth bound')]
    if pid==662:
        nodes=[[100,None,None]]
        for bits in ('0'*31,'1'*30+'0'):
            i=0
            for bit in bits:
                side=int(bit)+1
                if nodes[i][side] is None:nodes[i][side]=len(nodes);nodes.append([100,None,None])
                i=nodes[i][side]
        return [([chain(3000,100,True)],1,'3000-level skew must avoid positional overflow'),([_o.serialized(nodes)],2**31-1,'two paths attain maximum signed32 width')]
    if pid==664:return [(['a'*100],1,'single print'),(['ab'*50],51,'alternating100-character lower/upper bound')]
    if pid==671:
        nodes=[[1,None,None]]
        for i in range(12):nodes[i][1]=len(nodes);nodes.append([1,None,None]);nodes[i][2]=len(nodes);nodes.append([1,None,None])
        nodes[-1][0]=2**31-1;return [([_o.serialized(nodes)],2**31-1,'25-node full min-tree with maximum second value')]
    if pid==675:
        grid=[[i*50+(j+1 if i%2==0 else 50-j) for j in range(50)] for i in range(50)];grid[-1][0]=10**9
        return [([grid],2499,'50x50 consecutive snake, each move meets Manhattan lower bound')]
    if pid==676:
        words=[chr(97+i//26)+chr(97+i%26)+'a'*98 for i in range(100)];a=[['MagicDictionary','buildDict']+['search']*100,[[],[words]]+[[w] for w in words]];return [(a,reference(pid,a),'100 length100 words and100 searches')]
    if pid==677:
        ops=['MapSum'];argv=[[]]
        for i in range(25):key='a'*49+chr(97+i);ops+=['insert','sum'];argv += [[key,1000],[key]]
        a=[ops,argv];return [(a,reference(pid,a),'50 calls with length50 keys and maximum values')]
    if pid==679:return [([[9,9,9,9]],reference(pid,[[9,9,9,9]]),'all maximum-valued cards; full expression-tree enumeration')]
    if pid==687:
        nodes=_o.tree([1000]*10000);adj=[[] for _ in nodes]
        for i,(_,l,r) in enumerate(nodes):
            for j in (l,r):
                if j is not None:adj[i].append(j);adj[j].append(i)
        def far(start):
            q=deque([(start,-1,0)]);last=None
            while q:
                i,parent,d=q.popleft();last=(i,d);q.extend((j,i,d+1) for j in adj[i] if j!=parent)
            return last
        return [([[1000]*10000],far(far(0)[0])[1],'two-sweep undirected graph diameter'),([chain(1000,-1000)],999,'maximum permitted depth')]
    if pid==689:return [([[65535]*20000,6666],[0,6666,13332],'maximum n/value/k, tie resolves lexicographically')]
    if pid==690:return [([[[i,100,[i+1] if i<2000 else []] for i in range(1,2001)],1],200000,'2000-employee maximum-importance chain')]
    if pid==699:return [([[[10**8,10**6]]*1000],[i*10**6 for i in range(1,1001)],'1000 maximum-size squares with identical footprints')]
    if pid==700:return [([bst(range(1,5001)),10**7],[],'5000-node tree, maximum absent target'),([[10**7],10**7],[10**7],'maximum node value')]
    if pid==701:return [([bst(range(10000)),10**8],list(range(10000))+[10**8],'maximum input count; strict BST ordering/contents and fresh nodes checked')]
    if pid==703:return [([['KthLargest']+['add']*10000,[[10001,[-10000]*10000]]+[[10000]]*10000],[None]+[-10000]*10000,'maximum initial size/k/calls; kth value remains negative minimum')]
    if pid in (705,706):
        names=['add','contains','remove','contains'] if pid==705 else ['put','get','remove','get'];argv=[[10**6]]*4 if pid==705 else [[10**6,10**6],[10**6],[10**6],[10**6]];a=[[_o.CLASSES[pid]]+names*2500,[[]]+argv*2500];return [(a,reference(pid,a),'10000 calls with maximum keys/values')]
    if pid==707:return [([['MyLinkedList']+['addAtTail']*1999+['get'],[[]]+[[1000]]*1999+[[1000]]],[None]*2000+[1000],'2000 calls, maximum index/value')]
    if pid==710:
        a=[['Solution']+['pick']*20000,[[10**9,list(range(100000))]]+[[]]*20000];b=[['Solution']+['pick']*20000,[[100001,list(range(100000))]]+[[]]*20000]
        return [(a,reference(pid,a),'maximum n/blacklist/calls; support check'),(b,reference(pid,b),'maximum blacklist, single allowed result; rejection sampling pressure')]
    if pid==715:return [([['RangeModule','addRange']+['queryRange']*9999,[[],[1,10**9]]+[[1,10**9]]*9999],[None,None]+[True]*9999,'10000 calls at maximum right endpoint')]
    if pid==719:return [([[10**6]*10000,49995000],0,'all maximum-count pair distances are zero')]
    if pid==721:
        rows=[['A'*30]+[f'e{i:04d}x{j}@example.com' for j in range(9)] for i in range(1000)];return [([rows],sorted(rows),'1000 independent accounts,10 fields, maximum name length')]
    if pid==725:return [([[1000]*1000,50],[[1000]*20 for _ in range(50)],'1000 maximum-valued nodes,50 equal fresh parts')]
    raise ValueError(pid)


def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid in (589,590):
        args=[[{'values':[],'children':[]}]]
        for _ in range(20):
            n=rng.randrange(1,20);r={'values':[rng.randrange(10) for _ in range(n)],'children':[[] for _ in range(n)]}
            for i in range(1,n):r['children'][rng.randrange(i)].append(i)
            args.append([r])
    elif pid==600:args=[[n] for n in range(1,201)]
    elif pid in _o.TREE_IDS:
        if pid in (653,700,701):
            for _ in range(20):
                vs=sorted(rng.sample(range(1,100),rng.randrange(1,15)));args.append([bst(vs),rng.randrange(1,201) if pid==653 else rng.choice(vs+[101]) if pid==700 else 101])
            if pid==701:args.append([[],1])
        elif pid==671:args=[[[2,2,5,None,None,5,7]],[[2,2,2]],[[1]]]
        else:
            roots=[[1],[1,2,3,None,4],[1,None,2,3],[1,1,1,1,1,1,1]]+[[rng.randrange(-2,3) for _ in range(rng.randrange(1,16))] for _ in range(15)]
            for root in roots:
                if pid==617:args.extend([[root,[1,2,3]],[root,[]]])
                elif pid==623:
                    t=_o.tree(root);stack=[(0,1)];height=0
                    while stack:
                        i,d=stack.pop();height=max(height,d);stack.extend((j,d+1) for j in t[i][1:] if j is not None)
                    args.extend([[root,9,1],[root,-9,2],[root,9,height+1]])
                else:args.append([root])
            if pid==617:args.append([[],[]])
            if pid==687:args.append([[]])
    elif pid==629:args=[[n,k] for n in range(1,8) for k in range(n*(n-1)//2+2)]
    elif pid==630:args=[[[[rng.randrange(1,10),rng.randrange(1,30)] for _ in range(rng.randrange(1,9))]] for _ in range(30)]
    elif pid==632:args=[[[sorted(rng.randrange(-9,10) for _ in range(rng.randrange(1,4))) for _ in range(rng.randrange(1,5))]] for _ in range(30)]
    elif pid==639:args=[[''.join(xs)] for n in range(1,4) for xs in itertools.product('01*2',repeat=n)]+[['*0'],['1*'],['2*'],['3*']]
    elif pid==654:args=[[[*xs]] for n in range(1,6) for xs in itertools.permutations(range(n))]
    elif pid==664:args=[[''.join(xs)] for n in range(1,5) for xs in itertools.product('ab',repeat=n)]+[['aba'],['abc'],['abca']]
    elif pid==675:
        for _ in range(20):
            vs=rng.sample(range(2,50),6);g=[vs[:3],vs[3:]]
            for i in range(2):
                for j in range(3):
                    if rng.random()<.3:g[i][j]=0
            args.append([g])
        args.extend([[[[1,2,3],[0,0,4],[7,6,5]]],[[[1,2,3],[0,0,0],[7,6,5]]],[[[1]]]])
    elif pid==679:args=[[[4,1,8,7]],[[1,2,1,2]],[[3,3,8,8]],[[1,1,1,1]]]+[[[rng.randrange(1,10) for _ in range(4)]] for _ in range(18)]
    elif pid==689:args=[[[rng.randrange(1,20) for _ in range(n)],k] for n in range(3,13) for k in range(1,n//3+1)]
    elif pid==690:
        for _ in range(20):
            n=rng.randrange(1,20);es=[[i+1,rng.randrange(-100,101),[]] for i in range(n)]
            for i in range(1,n):es[rng.randrange(i)][2].append(i+1)
            args.append([es,rng.randrange(1,n+1)])
    elif pid==699:args=[[[[rng.randrange(1,20),rng.randrange(1,8)] for _ in range(rng.randrange(1,15))]] for _ in range(25)]
    elif pid==719:args=[[[rng.randrange(10) for _ in range(n)],rng.randrange(1,n*(n-1)//2+1)] for n in range(2,20) for _ in range(3)]
    elif pid==721:args=[[[['John','a@x.com','b@x.com'],['John','b@x.com','c@x.com'],['Mary','d@x.com']]],[[['A','a@x.com'],['A','a@x.com']]]]
    elif pid==725:args=[[list(range(n)),k] for n in range(12) for k in range(1,15)]
    elif pid in (622,641):
        names=['enQueue','deQueue','Front','Rear','isEmpty','isFull'] if pid==622 else ['insertFront','insertLast','deleteFront','deleteLast','getFront','getRear','isEmpty','isFull']
        for cap in (1,2,5):
            ops=[_o.CLASSES[pid]];argv=[[cap]]
            for _ in range(100):op=rng.choice(names);ops.append(op);argv.append([rng.randrange(1001)] if op in ('enQueue','insertFront','insertLast') else [])
            args.append([ops,argv])
    elif pid==676:args=[[['MagicDictionary','buildDict','search','search','search','search'],[[],[['hello','leetcode']],['hello'],['hhllo'],['hell'],['leetcoded']]],[['MagicDictionary','buildDict','search'],[[],[['a','b']],['a']]]]
    elif pid==677:args=[[['MapSum','insert','sum','insert','sum','insert','sum','sum'],[[],['apple',3],['ap'],['app',2],['ap'],['apple',2],['ap'],['apple']]]]
    elif pid==703:args=[[['KthLargest','add','add','add','add','add'],[[3,[4,5,8,2]],[3],[5],[10],[9],[4]]],[['KthLargest','add'],[[1,[]],[0]]]]
    elif pid in (705,706,707,715):
        names={705:['add','remove','contains'],706:['put','get','remove'],707:['get','addAtHead','addAtTail','addAtIndex','deleteAtIndex'],715:['addRange','queryRange','removeRange']}[pid]
        for _ in range(8):
            ops=[_o.CLASSES[pid]];argv=[[]]
            for _ in range(100):
                op=rng.choice(names);ops.append(op);a=[rng.randrange(15)]
                if op in ('put','addAtIndex'):a.append(rng.randrange(100))
                if pid==715:a=[rng.randrange(1,20),rng.randrange(20,35)]
                argv.append(a)
            args.append([ops,argv])
    elif pid==710:
        for n in range(1,7):
            for size in range(n):
                for black in itertools.combinations(range(n),size):
                    b=list(reversed(black));args.append([['Solution']+['pick']*(n-size),[[n,b]]+[[]]*(n-size)])
    if pid==715:
        args.extend([
            [['RangeModule','addRange','removeRange','queryRange','queryRange','queryRange'],[[],[10,20],[14,16],[10,14],[13,15],[16,17]]],
            [['RangeModule','addRange','addRange','queryRange','addRange','queryRange','removeRange','queryRange'],[[],[1,2],[3,4],[1,4],[2,3],[1,4],[2,3],[2,3]]]])
    if pid==721:
        args.extend([[[['A','a@x.com','b@x.com'],['A','c@x.com','d@x.com'],['A','b@x.com','c@x.com'],['A','solo@x.com']]],[[['A','a@x.com','a@x.com']]]])
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a,want,why in maximum(pid):validate_domain(pid,a);rows.append({'args':a,'expected':want,'category':'analytic-maximum','rationale':why,'isolate':True})
    return rows
