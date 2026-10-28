"""Public-definition cases plus fresh small exhaustive/seeded cases and analytic boundaries."""
import ast,html,json,re,random,string
from pathlib import Path
from itertools import product,permutations,combinations
import oracles as o

ROOT=Path(__file__).resolve().parents[4]
IMPORT=ROOT/'projects/algorithm_solver/catalogue/authored/downloaded-general60-v1'
ROWS=json.loads((IMPORT/'assignment.public-safe.json').read_text())['problems']
IDS=tuple(r['id']for r in ROWS)


def official(path,pid):
    q=json.loads(path.read_bytes())['data']['question']
    assert q and q['questionFrontendId']==str(pid)
    if not q['content']:return []
    body=html.unescape(re.sub('<[^>]+>',' ',q['content'])).replace('\u200b','').replace('\ufeff','')
    result=[]
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*\d+:|Constraints:|$)',body,re.S):
        node=ast.parse('f('+match[1].strip()+')',mode='eval').body
        assert isinstance(node,ast.Call)and not node.args and node.keywords
        args=[ast.literal_eval(k.value)for k in node.keywords]
        value,_=json.JSONDecoder().raw_decode(match[2].strip());result.append((args,value))
    assert result,pid
    return result


def build(statements=None):
    rng=random.Random(2026102806);data={i:[]for i in IDS};seen={i:set()for i in IDS};unset=object()
    def add(pid,args,category='independent-seeded-small',want=unset):
        key=json.dumps(args,separators=(',',':'))
        if key in seen[pid]:return
        seen[pid].add(key);data[pid].append({'args':args,'expected':o.expected(pid,args)if want is unset else want,'category':category})
    if statements:
        for pid in IDS:
            for args,value in official(Path(statements)/f'{pid}.json',pid):
                want=o.expected(pid,args);assert o.matches(pid,args,value,want),(pid,args,value,want)
                add(pid,args,'official-example')
    for n in range(1,8):
        for bits in product((0,1),repeat=n-1):add(717,[[*bits,0]],'exhaustive-binary-prefix')
    for n in range(2,6):
        for values in product((-2,-1,1,2),repeat=n):add(735,[list(values)],'exhaustive-collision-signs')
    for p in permutations(range(6)):add(773,[[list(p[:3]),list(p[3:])]],'complete-puzzle-domain')
    for cells in product(' XO',repeat=9):add(794,[[''.join(cells[:3]),''.join(cells[3:6]),''.join(cells[6:])]],'complete-tictactoe-domain')
    for n in range(1,7):
        for cells in product('LR.',repeat=n):add(838,[''.join(cells)],'exhaustive-synchronous-force')
    for n in range(1,8):
        for values in product((0,1,2),repeat=n):
            if n<=5:add(768,[list(values)],'exhaustive-chunk-partitions')
    for n in range(1,7):
        for p in permutations(range(n)):
            add(769,[list(p)],'exhaustive-permutation-chunks');add(775,[list(p)],'exhaustive-inversion-counts')
    for n in range(101):add(738,[n],'monotone-digit-neighbors')
    for n in (1110,1234,332,987654321,999999999,1000000000):add(738,[n],'decimal-boundaries')
    for t in (*range(-100,0),*range(1,101),-10**9,10**9):add(754,[t],'signed-reachability')
    for n in range(1,11):
        for k in range(1,(1<<(n-1))+1):add(779,[n,k],'complete-short-grammar-rows')
    for n in (15,20,30):
        for k in (1,2,1<<(n-2),(1<<(n-1))-1,1<<(n-1)):add(779,[n,k],'grammar-maximum-position')
    for n in [*range(1,101),9999,10000]:add(788,[n],'rotated-decimal-bounds')
    for n in [*range(1,21),100,1000]:add(790,[n],'independent-exact-cover-transfer')
    for k in [*range(101),305175780,305175781,10**9]:add(793,[k],'factorial-valuation-gaps')
    for n in [*range(1,101),10**9,999999937]:add(829,[n],'odd-divisor-counts')
    for _ in range(60):
        s=''.join(rng.choices('abcxyz',k=rng.randint(1,8)));t=''.join(rng.choices('abcxyz',k=rng.randint(1,8)))
        add(712,[s,t]);xs=[rng.randint(1,6)for _ in range(rng.randint(1,8))];add(713,[xs,rng.randint(0,60)])
        add(714,[[rng.randint(1,20)for _ in range(rng.randint(1,8))],rng.randint(0,8)])
        add(718,[[rng.randrange(5)for _ in range(rng.randint(1,8))],[rng.randrange(5)for _ in range(rng.randint(1,8))]])
        word=''.join(rng.choices('abc',k=rng.randint(1,6)));words=[word[:i]for i in range(1,len(word)+1)]+[s,t];rng.shuffle(words);add(720,[words])
        comments=[['a/*','x*/b'],['a//gone','b'],['/*gone*/'],['a/*x*/b//end'],['a','/**/','b'],['/*/a/*b*/c'],['x// /* ignored','y'],['a/*x','y','z*/b']];add(722,[rng.choice(comments)])
        add(740,[[rng.randint(1,8)for _ in range(rng.randint(1,8))]])
        n=rng.randint(2,6);edges=[]
        for u,v in permutations(range(1,n+1),2):
            if rng.randrange(4)==0:edges.append([u,v,rng.randrange(20)])
        if not edges:edges=[[1,2,1]]
        add(743,[edges,n,rng.randint(1,n)])
        add(746,[[rng.randrange(21)for _ in range(rng.randint(2,10))]])
        need=''.join(rng.choices('abc',k=rng.randint(1,3)));license=need.upper()+' 17';word=need+''.join(rng.choices('xyz',k=rng.randrange(4)));words=[s,t,word,word+'x'];add(748,[license,words])
        target=rng.choice(['0000','0001','0009','0010','9000','9900','0011','0101']);dead=[f'{rng.randrange(10000):04d}'for _ in range(rng.randint(1,10))];dead=sorted(set(dead)-{target})or['8888'];add(752,[dead,target])
        arr=[rng.randint(0,20)for _ in range(rng.randint(1,8))];copy=arr[:];rng.shuffle(copy);add(760,[arr,copy])
        add(763,[s]);n=rng.randint(1,5);mines=[list(p)for p in product(range(n),repeat=2)if rng.randrange(3)==0];add(764,[n,mines])
        rows,cols=rng.randint(1,4),rng.randint(1,4);matrix=[[rng.randrange(5)for _ in range(cols)]for _ in range(rows)];add(766,[matrix])
        length=rng.randint(1,7);start=''.join(rng.choices('LRX',k=length));end=''.join(rng.choices('LRX',k=length));add(777,[start,end])
        n=rng.randint(1,4);arr=rng.sample(range(n*n),n*n);add(778,[[arr[i*n:(i+1)*n]for i in range(n)]])
        add(780,[rng.randint(1,4),rng.randint(1,4),rng.randint(1,24),rng.randint(1,24)])
        add(781,[[rng.randrange(10)for _ in range(rng.randint(1,10))]])
        n=rng.randint(1,7);graph=[[]for _ in range(n)]
        for i,j in combinations(range(n),2):
            if rng.randrange(3)==0:graph[i].append(j);graph[j].append(i)
        add(785,[graph]);primes=sorted(rng.sample([2,3,5,7,11,13,17,19,23],rng.randint(1,6)));arr=[1]+primes;add(786,[arr,rng.randint(1,len(arr)*(len(arr)-1)//2)])
        n=rng.randint(2,6);flights=[]
        for u,v in combinations(range(n),2):
            if rng.randrange(3)==0:
                if rng.randrange(2):u,v=v,u
                flights.append([u,v,rng.randint(1,30)])
        src,dst=rng.sample(range(n),2);add(787,[n,flights,src,dst,rng.randrange(n)])
        add(789,[[[rng.randint(-4,4),rng.randint(-4,4)]for _ in range(rng.randint(1,5))],[rng.randint(-4,4),rng.randint(-4,4)]])
        order=''.join(rng.sample('abcxyz',rng.randint(1,6)));add(791,[order,s]);words=[''.join(rng.choices('abcxyz',k=rng.randint(1,6)))for _ in range(rng.randint(1,8))];add(792,[s,words])
        lo=rng.randrange(7);hi=rng.randint(lo,9);add(795,[[rng.randrange(10)for _ in range(rng.randint(1,9))],lo,hi])
        n=rng.randint(2,7);graph=[[]for _ in range(n)]
        for i,j in combinations(range(n),2):
            if rng.randrange(3)==0:graph[i].append(j)
        add(797,[graph]);n=rng.randint(2,4);add(807,[[[rng.randrange(20)for _ in range(n)]for _ in range(n)]])
        add(810,[[rng.randrange(8)for _ in range(rng.randint(1,8))]])
        add(811,[[str(rng.randint(1,100))+' '+rng.choice(['a.com','b.com','a.b.com','x.a.com'])for _ in range(rng.randint(1,6))]])
        winner,other,bannedword=rng.sample(['alpha','beta','gamma','delta','omega'],3);banned=[bannedword]if rng.randrange(2)else[]
        tokens=[winner]*4+[other]*2+[bannedword]*(5 if banned else 1);rng.shuffle(tokens)
        paragraph=''.join((word.upper()if rng.randrange(2)else word)+rng.choice([' ',"!","?","'",',',';','.'])for word in tokens)
        add(819,[paragraph,banned])
        add(820,[[''.join(rng.choices('abc',k=rng.randint(1,6)))for _ in range(rng.randint(1,7))]])
        n=rng.randint(1,7);add(822,[[rng.randint(1,8)for _ in range(n)],[rng.randint(1,8)for _ in range(n)]])
        add(825,[[rng.randint(1,120)for _ in range(rng.randint(1,12))]])
        n=rng.randint(1,8);add(826,[[rng.randint(1,30)for _ in range(n)],[rng.randint(1,30)for _ in range(n)],[rng.randint(1,30)for _ in range(rng.randint(1,8))]])
        name=''.join(rng.choices(string.ascii_letters,k=rng.randint(2,12)));add(831,[name+'@Example.COM']);digits=''.join(rng.choices(string.digits,k=rng.randint(10,13)));add(831,['+'+digits[:3]+' '+digits[3:]])
        indices=rng.sample(range(len(s)),rng.randint(1,len(s)));sources=[s[i]if rng.randrange(2)else'z'for i in indices];targets=[''.join(rng.choices('abc',k=rng.randint(1,4)))for _ in indices];add(833,[s,indices,sources,targets])
        n=rng.randint(1,4);add(835,[[[rng.randrange(2)for _ in range(n)]for _ in range(n)],[[rng.randrange(2)for _ in range(n)]for _ in range(n)]])
        chars=list(''.join(rng.choices('abc',k=rng.randint(1,6))));strs=[]
        for i in range(rng.randint(1,8)):rng.shuffle(chars);strs.append(''.join(chars))
        add(839,[strs]);rows,cols=rng.randint(1,5),rng.randint(1,5);add(840,[[[rng.randrange(16)for _ in range(cols)]for _ in range(rows)]])
        n=rng.randint(2,8);rooms=[rng.sample(range(n),rng.randrange(n))for _ in range(n)];add(841,[rooms])
        add(845,[[rng.randrange(8)for _ in range(rng.randint(1,10))]])
        hand=[rng.randrange(7)for _ in range(rng.randint(1,9))];add(846,[hand,rng.randint(1,len(hand))])
        add(848,[s,[rng.randint(0,10**9)for _ in s]])
        seats=[rng.randrange(2)for _ in range(rng.randint(2,12))]
        if 0 in seats and 1 in seats:add(849,[seats])
    for args in [[['0000'],'0001'],[['8888'],'0000'],[['0001','0009','0010','0090','0100','0900','1000','9000'],'1111']]:add(752,args,'blocked-start-and-boundaries')
    magic=[[4,3,8],[9,5,1],[2,7,6]]
    for _ in range(4):
        add(840,[magic],'lo-shu-positive');add(840,[[row[::-1]for row in magic]],'lo-shu-positive');magic=[list(row)for row in zip(*magic[::-1])]
    add(792,['a'*50000,['b'*50]*5000],'maximum-size-negative-subsequence',want=0)
    add(768,[list(range(1999,-1,-1))],'maximum-size-descending',want=1)
    add(778,[[list(range(r*50,(r+1)*50))for r in range(50)]],'maximum-square-endpoint-bound',want=2499)
    add(849,[[1]+[0]*19999],'maximum-seat-gap',want=19999)
    add(712,['a'*1000,'b'*1000],'maximum-distinct-ASCII-strings',want=195000)
    add(718,[[1]*1000,[2]*1000],'maximum-disjoint-arrays',want=0)
    add(746,[[999]*1000],'maximum-stair-cost',want=499500)
    add(763,['a'*500],'maximum-single-partition',want=[500])
    add(764,[500,[]],'maximum-empty-plus-grid',want=250)
    primes=[n for n in range(2,8000)if all(n%d for d in range(2,__import__('math').isqrt(n)+1))][:999]
    add(786,[[1]+primes,1],'maximum-prime-fraction-population',want=[1,primes[-1]])
    add(807,[[[0]*50 for _ in range(50)]],'maximum-empty-skyline',want=0)
    add(810,[[0]*1000],'maximum-zero-XOR',want=True)
    add(820,[['a'*7]*2000],'maximum-duplicate-encoding',want=8)
    add(825,[[120]*20000],'maximum-equal-age-requests',want=20000*19999)
    add(826,[[1]*10000,[1]*10000,[1]*10000],'maximum-job-worker-count',want=10000)
    add(848,['a'*100000,[10**9]*100000],'maximum-prefix-shifts',want=''.join(chr(97+((100000-i)*10**9)%26)for i in range(100000)))
    add(839,[['a'*300]*300],'maximum-identical-anagram-group',want=1)
    for pid in IDS:assert data[pid],pid
    return data
