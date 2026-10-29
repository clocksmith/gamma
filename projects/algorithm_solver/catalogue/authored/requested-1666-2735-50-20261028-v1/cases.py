"""Bounded brute-force models and explicitly justified maximum-domain cases."""
import importlib.util
from pathlib import Path
import itertools,random,math
from collections import deque
_spec=importlib.util.spec_from_file_location('gamma_public51_cases_'+Path(__file__).parent.name,Path(__file__).with_name('oracles.py'));O=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(O)
reference,validate_domain=O.reference,O.validate_domain


def chain_values(values,right=False):
    rows=[[v,None,i+1 if i+1<len(values) else None] if right else [v,i+1 if i+1<len(values) else None,None] for i,v in enumerate(values)]
    return O.serialized(rows)


def bst(values):
    rows=[]
    def make(xs):
        if not xs:return None
        mid=len(xs)//2;i=len(rows);rows.append([xs[mid],None,None]);rows[i][1]=make(xs[:mid]);rows[i][2]=make(xs[mid+1:]);return i
    return O.serialized(rows,make(list(values)))


def maximum(pid):
    if pid==963:return [([[[0,0],[40000,0],[40000,40000],[0,40000]]+[[i,0] for i in range(1,47)]],1600000000,'50 points on two horizontal lines force the large rectangle')]
    if pid==964:return [([100,200000000],7,'two x^4 terms require7 operators; shorter bounded-degree expressions cannot attain2*x^4'),([100,1],1,'x/x')]
    if pid==968:return [([chain_values([0]*1000)],334,'minimum dominating set of1000-node path has ceil(n/3) cameras')]
    if pid==969:return [([list(range(100,0,-1))],{'kind':'pancake','sorted':list(range(1,101))},'maximum permutation length; validate flips and official operation bound')]
    if pid==975:return [([[99999]*20000],20000,'all next jumps can advance one position at maximum length/value')]
    if pid==979:return [([chain_values([100]+[0]*99)],4950,'all100 coins at path root require sum(0..99) edge traversals')]
    if pid==980:return [([[[1]+[0]*18+[2]]],1,'20-cell horizontal Hamiltonian corridor'),([[[1]]+[[0]]*18+[[2]]],1,'20-cell vertical Hamiltonian corridor')]
    if pid==981:
        ops=['TimeMap']+['set']*100000+['get']*100000;args=[[]]+[['a'*100,'b'*100,i] for i in range(1,100001)]+[['a'*100,10000000]]*100000
        return [([ops,args],[None]*100001+['b'*100]*100000,'200000 calls,100-character strings, maximum query timestamp')]
    if pid==982:return [([[0]*1000],1000000000,'every ordered triple qualifies'),([[65535]*1000],0,'maximum values have nonzero triple AND')]
    if pid==984:return [([100,100],{'kind':'two-letter','a':100,'b':100},'both letter counts at maximum'),([100,49],{'kind':'two-letter','a':100,'b':49},'tight feasibility bound')]
    if pid==985:return [([[10000]*10000,[[10000,0]]*10000],[100000000+10000*i for i in range(1,10001)],'maximum array/query count and increments; every value remains even')]
    if pid==987:
        a=[[1000]*1000];return [(a,reference(pid,a),'independent coordinate buckets on1000 maximum-valued nodes')]
    if pid==993:return [([list(range(1,101)),99,100],True,'100 nodes and two same-depth distinct-parent targets')]
    if pid==994:return [([[[2]+[1]*9]+[[1]*10 for _ in range(9)]],18,'10x10 grid Manhattan diameter from one source')]
    if pid==996:return [([[1000000000]*12],0,'maximum values cannot make a square adjacent sum'),([[1]*6+[8]*6],7,'six1s must occupy six of seven gaps around six8s')]
    if pid==999:
        board=[list('pppppppp') for _ in range(8)];board[3][3]='R';return [([board],4,'every direction immediately meets one pawn')]
    if pid==1000:return [([[100]*30,2],14800,'optimal equal-weight alphabetic binary merge leaf depths4/5'),([[100]*30,30],3000,'single maximum-k merge')]
    if pid==1012:return [([1000000000],1000000000-sum(9*math.perm(9,k-1) for k in range(1,10)),'all unique-digit positive integers have at most9 digits under this ceiling')]
    if pid==1019:return [([list(range(1,10001))],list(range(2,10001))+[0],'10000 increasing nodes'),([[1000000000]*10000],[0]*10000,'maximum values never find a strictly greater successor')]
    if pid==1022:return [([[0]*1000],0,'maximum node count with zero path values'),([chain_values([1]*31)],2147483647,'maximum guaranteed signed32 result')]
    if pid==1028:return [([''.join('-'*i+'1000000000' for i in range(1000))],chain_values([1000000000]*1000),'1000-depth left-only encoding with maximum node values')]
    if pid==1032:return [([['StreamChecker']+['query']*40000,[[['a'*200]*2000]]+[['a']]*40000],[None]+[False]*199+[True]*(40000-199),'2000 length200 words and40000 queries')]
    if pid==1038:
        a=[bst(range(100))];return [(a,reference(pid,a),'100 distinct nodes and independent all-greater-value sums'),([[100]],[100],'maximum node value')]
    if pid==1040:return [([list(range(1,10000))+[1000000000]],[2,999990000],'endpoint-only near-consecutive special case at maximum count/coordinate')]
    if pid==1054:return [([[10000]*5000+[1]*5000],{'kind':'barcodes','counts':[(1,5000),(10000,5000)]},'maximum length/value with tight multiplicity feasibility')]
    if pid==1095:
        mountain=list(range(9999))+[9997];mountain[9998]=1000000000
        return [([1000000000,mountain],9998,'10000-item mountain, maximum peak value; observer enforces100 gets'),([999999999,mountain],-1,'absent maximum-scale target checks both halves')]
    if pid==1096:
        expression='aaaa'+'{a,b,c}'*8;words=sorted('aaaa'+''.join(p) for p in itertools.product('abc',repeat=8));return [([expression],words,'length60 Cartesian grammar expansion, independently enumerated')]
    if pid==1110:return [([list(range(1,1001)),list(range(1,1001))],[],'maximum nodes/deletion count; every node removed')]
    if pid==1138:return [(['zb'*50],{'kind':'board-path','target':'zb'*50},'maximum length repeatedly crosses the z boundary')]
    if pid==1146:return [([['SnapshotArray','set','snap']+['get']*49998,[[50000],[49999,1000000000],[]]+[[49999,0]]*49998],[None,None,0]+[1000000000]*49998,'50000 calls at maximum index/value'),([['SnapshotArray']+['snap']*50000,[[50000]]+[[]]*50000],[None]+list(range(50000)),'maximum snapshot count')]
    if pid==1147:return [(['a'*1000],1000,'each character is a matching outer chunk')]
    if pid==1157:return [([['MajorityChecker']+['query']*10000,[[[20000]*20000]]+[[0,19999,20000]]*10000],[None]+[20000]*10000,'maximum array/query count/value and threshold')]
    if pid==1172:return [([['DinnerPlates']+['push']*100000+['pop']*100000,[[20000]]+[[20000]]*100000+[[]]*100000],[None]*100001+[20000]*100000,'200000 calls, maximum capacity/value'),([['DinnerPlates','popAtStack'],[[20000],[100000]]],[None,-1],'maximum index parameter')]
    if pid==1191:return [([[10000]*100000,100000],(10**14)%O.MOD,'maximum positive total before modular reduction'),([[-10000]*100000,100000],0,'empty subarray beats all-negative copies')]
    if pid==1206:return [([['Skiplist']+['add']*25000+['erase']*25000,[[]]+[[20000]]*50000],[None]*25001+[True]*25000,'50000 calls, duplicates at maximum value')]
    if pid==1669:
        a=list(range(10000));b=[1000000]*10000;return [([a,1,9998,b],[a[0]]+b+[a[-1]],'both maximum list lengths and widest valid interior splice')]
    if pid==1670:return [([['FrontMiddleBackQueue']+['pushMiddle']*500+['popMiddle']*500,[[]]+[[1000000000]]*500+[[]]*500],[None]*501+[1000000000]*500,'1000 calls, maximum value')]
    if pid==1674:return [([[100000]*100000,100000],0,'maximum length and limit, already complementary')]
    if pid==1712:return [([[0]*100000],((99999*99998)//2)%O.MOD,'all ordered pairs of nonempty split boundaries qualify')]
    if pid==1718:return [([20],{'kind':'distanced-sequence','n':20},'maximum-n validity checked; lexicographic optimality relies on descending-search argument, not a brute maximum oracle')]
    if pid==1728:return [([['M......F']+['........']*6+['C.......'],8,8],True,'8x8 open board, mouse reaches food on its first maximum jump')]
    if pid==1786:return [([20000,[[i,i+1,100000] for i in range(1,20000)]],1,'maximum n/weight, unique restricted path'),([284,[[i,j,1] for i in range(1,285) for j in range(i+1,285)][:40000]],1,'40000 edges; only direct destination edges strictly decrease distance in near-complete graph')]
    if pid==1797:
        ops=['AuthenticationManager','generate']+['countUnexpiredTokens']*1999;argv=[[100000000],['aaaaa',1]]+[[100000000-i] for i in range(1998,-1,-1)];return [([ops,argv],[None,None]+[1]*1999,'2000 calls, maximum ttl/time, strict increasing calls')]
    if pid==1825:return [([['MKAverage']+['addElement']*99999+['calculateMKAverage'],[[99999,49999]]+[[100000]]*99999+[[]]],[None]*100000+[100000],'100000 calls, largest odd full window and trimming tails'),([['MKAverage','calculateMKAverage'],[[100000,49999],[]]],[None,-1],'maximum m before full window')]
    if pid==1840:return [([1000000000,[[i,0] for i in range(2,100002)]],999899999,'100000 zero restrictions fix initial segment; remainder rises by one per building'),([1000000000,[[1000000000,1000000000]]],999999999,'maximum height allowance cannot exceed slope from building1')]
    if pid==1845:return [([['SeatManager']+['reserve']*100000,[[100000]]+[[]]*100000],[None]+list(range(1,100001)),'maximum capacity and call count')]
    if pid==1865:return [([['FindSumPairs']+['count']*1000,[[[100000]*1000,[100000]*100000]]+[[200000]]*1000],[None]+[100000000]*1000,'maximum array lengths/count calls, every pair qualifies'),([['FindSumPairs','add','count'],[[[1000000000],[100000]],[0,100000],[1000000000]]],[None,None,0],'maximum first-array value and increment')]
    if pid==1912:
        entries=[[i,10000,10000] for i in range(100000)];a=[['MovieRentingSystem']+['search']*100000,[[300000,entries]]+[[10000]]*100000];return [(a,[None]+[[0,1,2,3,4]]*100000,'maximum shop/entry/call count, movie and price; deterministic top5 ties')]
    if pid==2025:return [([[0]*100000,0],99999,'every split stays balanced at maximum length'),([[100000]*100000,-100000],1,'unchanged even split is optimal; replacement cannot add more')]
    if pid==2060:return [(['a'*40,'a'*40],True,'maximum literal lengths'),(['a'*40,'b'*40],False,'maximum unequal literals'),(['999a'*10,'999a'*10],True,'maximum length with three-digit runs')]
    if pid==2735:return [([[1000000000]*1000,1000000000],1000000000000,'maximum costs/rotation fee; rotations cannot improve equal prices')]
    raise ValueError(pid)


def build_cases(pid,include_maximum=False):
    rng=random.Random(2026102800+pid);args=[]
    if pid==963:args=[[[[0,0],[1,1],[1,0],[0,1]]],[[[0,1],[1,0],[2,1],[1,2]]]]+[[[list(p) for p in rng.sample(list(itertools.product(range(5),repeat=2)),rng.randrange(1,10))]] for _ in range(12)]
    elif pid==964:args=[[x,t] for x in range(2,6) for t in range(1,21)]
    elif pid in O.TREE_IDS:
        if pid==993:args=[[[1,2,3,4,None,None,5],4,5],[[1,2,3,4,5],4,5],[[1,2],1,2]]
        elif pid==1038:args=[[bst(sorted(rng.sample(range(101),rng.randrange(1,15))))] for _ in range(15)]
        else:
            for _ in range(15):
                n=rng.randrange(1,8)
                if pid==968:root=[0]*n
                elif pid==979:
                    root=[0]*n
                    for _ in range(n):root[rng.randrange(n)]+=1
                elif pid==1022:root=[rng.randrange(2) for _ in range(n)]
                elif pid==1110:root=rng.sample(range(1,1001),n)
                else:root=[rng.randrange(10) for _ in range(n)]
                args.append([root,rng.sample(root,rng.randrange(n+1))] if pid==1110 else [root])
    elif pid==969:args=[[[*p]] for n in range(1,7) for p in itertools.permutations(range(1,n+1))]
    elif pid==975:args=[[[rng.randrange(5) for _ in range(n)]] for n in range(1,20) for _ in range(2)]
    elif pid==980:
        for start,end in itertools.permutations(range(6),2):
            grid=[[0]*3 for _ in range(2)];grid[start//3][start%3]=1;grid[end//3][end%3]=2;args.append([grid])
    elif pid==982:args=[]
    elif pid==984:args=[[a,b] for a in range(9) for b in range(9) if max(a,b)<=2*(min(a,b)+1)]
    elif pid==985:
        for _ in range(20):
            a=[rng.randrange(-10,11) for _ in range(8)];args.append([a,[[rng.randrange(-10,11),rng.randrange(8)] for _ in range(12)]])
    elif pid==994:args=[[[list(p[:2]),list(p[2:])]] for p in itertools.product(range(3),repeat=4)]
    elif pid==996:args=[[[rng.choice([0,1,2,8,9,16]) for _ in range(n)]] for n in range(1,8) for _ in range(3)]
    elif pid==999:
        for _ in range(20):
            board=[[rng.choice('.Bp') for _ in range(8)] for _ in range(8)];r,c=rng.randrange(8),rng.randrange(8);board[r][c]='R';args.append([board])
    elif pid==1000:args=[[[rng.randrange(1,10) for _ in range(n)],k] for n in range(1,9) for k in range(2,5)]
    elif pid==1012:args=[[n] for n in range(1,201)]+[[999],[1000],[1234]]
    elif pid==1019:args=[[[rng.randrange(1,20) for _ in range(n)]] for n in range(1,25)]
    elif pid==1028:args=[]
    elif pid==1040:args=[[[*xs]] for n in range(3,6) for xs in itertools.combinations(range(1,9),n)]
    elif pid==1054:args=[[[*xs]] for n in range(1,7) for xs in itertools.combinations_with_replacement([1,2,3],n) if max(O.Counter(xs).values())<=(n+1)//2]
    elif pid==1095:args=[[t,[1,3,5,8,6,3,0]] for t in range(10)]+[[2,[0,2,1]]]
    elif pid==1096:args=[[s] for s in ['a','{a,b}','{a,b}{c,{d,e}}','{{a,z},a{b,c},{ab,z}}','a{b,c}d','{{a,b},{b,c}}']]
    elif pid==1138:args=[[s] for s in ['a','z','zb','bz','azaz','leetcode','zdz','zzzzz']]
    elif pid==1147:args=[[''.join(p)] for n in range(1,8) for p in itertools.product('ab',repeat=n)]+[['ghiabcdefhelloadamhelloabcdefghi']]
    elif pid==1191:args=[[[rng.randrange(-5,6) for _ in range(n)],k] for n in range(1,8) for k in range(1,5)]
    elif pid==1669:args=[[list(range(n)),a,b,[99,100]] for n in range(3,9) for a in range(1,n-1) for b in range(a,n-1)]
    elif pid==1674:args=[[[rng.randrange(1,limit+1) for _ in range(n)],limit] for limit in range(1,8) for n in (2,4,6,8)]
    elif pid==1712:args=[[[*xs]] for n in range(3,7) for xs in itertools.product([0,1,2],repeat=n)]
    elif pid==1718:args=[[n] for n in range(1,5)]
    elif pid==1728:args=[[[s],cat,mouse] for s in ['MCF','M.CF','M.C.F','CM.F'] for cat in (1,2) for mouse in (1,2)]+[[['M#F','..C'],1,1]]
    elif pid==1786:
        for n in range(1,8):
            for _ in range(3):
                pairs={(i,i+1) for i in range(1,n)};pairs.update((i,j) for i in range(1,n+1) for j in range(i+1,n+1) if rng.random()<.2);args.append([n,[[i,j,rng.randrange(1,10)] for i,j in pairs]])
    elif pid==1840:args=[[n,[[i,rng.randrange(5)] for i in range(2,n+1) if rng.random()<.4]] for n in range(2,9) for _ in range(3)]
    elif pid==2025:args=[[[*xs],k] for n in range(2,6) for xs in itertools.product([-1,0,1],repeat=n) for k in (-1,1)]
    elif pid==2060:args=[[a,b] for a,b in itertools.product(['a','b','1','2','3','a1','1a','12','a2b','2b'],repeat=2)]+[['internationalization','i18n'],['l123e','44']]
    elif pid==2735:args=[[[rng.randrange(1,20) for _ in range(n)],rng.randrange(1,20)] for n in range(1,10) for _ in range(3)]
    elif pid in O.CLASSES:args=class_cases(pid,rng)
    if pid==982:args=[[[rng.randrange(16) for _ in range(rng.randrange(1,7))]] for _ in range(10)]
    if pid==1028:args=[['1'],['1-2--3--4-5--6--7'],['10-20--30---40-50']]+[[''.join('-'*i+str(i+1) for i in range(n))] for n in range(2,12)]
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if include_maximum:
        for a,want,why in maximum(pid):validate_domain(pid,a);rows.append({'args':a,'expected':want,'category':'analytic-maximum','rationale':why,'isolate':True})
    return rows


def class_cases(pid,rng):
    result=[]
    for _ in range(8):
        ops=[O.CLASSES[pid]];argv=[]
        if pid==981:
            argv=[[]];time=0
            for j in range(40):
                if rng.random()<.6:time+=rng.randrange(1,4);ops.append('set');argv.append([rng.choice('abc'),rng.choice('def'),time])
                else:ops.append('get');argv.append([rng.choice('abc'),rng.randrange(1,time+3)])
        elif pid==1032:ops+=['query']*80;argv=[[['ab','bc','aaa']]]+[[rng.choice('abc')] for _ in range(80)]
        elif pid==1146:
            argv=[[5]];snaps=0
            for j in range(50):
                op=rng.choice(['set','snap']+(['get'] if snaps else []));ops.append(op)
                if op=='set':argv.append([rng.randrange(5),rng.randrange(20)])
                elif op=='snap':argv.append([]);snaps+=1
                else:argv.append([rng.randrange(5),rng.randrange(snaps)])
        elif pid==1157:
            xs=[rng.randrange(1,6) for _ in range(20)];argv=[[xs]]
            for j in range(40):l=rng.randrange(20);r=rng.randrange(l,20);ops.append('query');argv.append([l,r,rng.randrange((r-l+1)//2+1,r-l+2)])
        elif pid==1172:
            argv=[[rng.randrange(1,5)]]
            for j in range(100):op=rng.choice(['push','pop','popAtStack']);ops.append(op);argv.append([rng.randrange(1,30)] if op=='push' else [rng.randrange(20)] if op=='popAtStack' else [])
        elif pid==1206:
            argv=[[]]
            for j in range(100):ops.append(rng.choice(['add','erase','search']));argv.append([rng.randrange(10)])
        elif pid==1670:
            argv=[[]]
            for j in range(100):op=rng.choice(['pushFront','pushMiddle','pushBack','popFront','popMiddle','popBack']);ops.append(op);argv.append([rng.randrange(1,100)] if op.startswith('push') else [])
        elif pid==1797:
            argv=[[rng.randrange(1,10)]];generated=[]
            for j in range(50):
                op=rng.choice(['generate','renew','countUnexpiredTokens']);ops.append(op)
                if op=='generate':token=chr(97+j//26)+chr(97+j%26);generated.append(token);argv.append([token,j+1])
                elif op=='renew':argv.append([rng.choice(generated) if generated else 'z',j+1])
                else:argv.append([j+1])
        elif pid==1825:
            argv=[[7,2]]
            for j in range(80):op=rng.choice(['addElement']*3+['calculateMKAverage']);ops.append(op);argv.append([rng.randrange(1,20)] if op=='addElement' else [])
        elif pid==1845:
            argv=[[10]];reserved=set()
            for j in range(80):
                if not reserved or len(reserved)<10 and rng.random()<.6:ops.append('reserve');argv.append([]);reserved.add(next(i for i in range(1,11) if i not in reserved))
                else:seat=rng.choice(sorted(reserved));ops.append('unreserve');argv.append([seat]);reserved.remove(seat)
        elif pid==1865:
            argv=[[[rng.randrange(1,10) for _ in range(5)],[rng.randrange(1,10) for _ in range(7)]]]
            for j in range(50):op=rng.choice(['add','count']);ops.append(op);argv.append([rng.randrange(7),rng.randrange(1,10)] if op=='add' else [rng.randrange(1,40)])
        elif pid==1912:
            entries=[[s,m,rng.randrange(1,10)] for s in range(5) for m in range(1,5)];argv=[[5,entries]];available={(s,m) for s,m,_ in entries};rented=set()
            for j in range(100):
                options=['search','report']+(['rent'] if available else [])+(['drop'] if rented else []);op=rng.choice(options);ops.append(op)
                if op=='search':argv.append([rng.randrange(1,6)])
                elif op=='report':argv.append([])
                elif op=='rent':pair=rng.choice(sorted(available));argv.append(list(pair));available.remove(pair);rented.add(pair)
                else:pair=rng.choice(sorted(rented));argv.append(list(pair));rented.remove(pair);available.add(pair)
        result.append([ops,argv])
    return result
