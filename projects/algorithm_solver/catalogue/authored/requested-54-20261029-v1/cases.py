"""Small oracle cases and independently justified boundaries are separate streams."""
import random
from itertools import product,combinations
IDS=[827,828,847,851,854,862,864,872,882,894,895,902,906,920,927,932,952,960]

def small_cases():
    rng=random.Random(54029)
    for n in range(1,4):
        for bits in product(range(2),repeat=n*n):yield 827,[[list(bits[r*n:(r+1)*n]) for r in range(n)]]
    for n in range(1,7):
        for chars in product('AB',repeat=n):yield 828,[''.join(chars)]
    for n in range(1,5):
        pairs=list(combinations(range(n),2))
        for bits in product(range(2),repeat=len(pairs)):
            g=[[] for _ in range(n)]
            for (a,b),on in zip(pairs,bits):
                if on:g[a].append(b);g[b].append(a)
            seen={0};front=[0]
            for a in front:
                for b in g[a]:
                    if b not in seen:seen.add(b);front.append(b)
            if len(seen)==n:yield 847,[g]
    for _ in range(40):
        n=rng.randint(1,8);order=rng.sample(range(n),n);quiet=rng.sample(range(n),n)
        edges=[[order[i],order[j]] for i in range(n) for j in range(i+1,n) if rng.random()<.4]
        yield 851,[edges,quiet]
    for n in range(1,6):
        for chars in product('abc',repeat=n):
            s=''.join(chars);yield 854,[s,s[::-1]]
    for n in range(1,6):
        for nums in product([-2,0,3],repeat=n):
            for k in [1,4,8]:yield 862,[list(nums),k]
    for s in ['@aA','@Aa','aA@','a@A','A@a','Aa@','@.a.A','@#aA','@..aA']:
        yield 864,[[s]]
    for _ in range(50):
        chars=['@','a','A','b','B']+[rng.choice('.#') for _ in range(4)];rng.shuffle(chars)
        yield 864,[[''.join(chars[i:i+3]) for i in range(0,9,3)]]
    def random_tree(n):
        if n==0:return None
        l=rng.randrange(n);return [rng.randrange(201),random_tree(l),random_tree(n-1-l)]
    for _ in range(35):
        t=random_tree(rng.randint(1,15));u=t if rng.random()<.5 else random_tree(rng.randint(1,15));yield 872,[t,u]
    for _ in range(90):
        n=rng.randint(1,6);edges=[[a,b,rng.randrange(4)] for a in range(n) for b in range(a+1,n) if rng.random()<.35]
        yield 882,[edges,rng.randrange(15),n]
    for n in range(1,12):yield 894,[n]
    def traces(ops,rows,size,remaining):
        if not remaining:yield 895,[ops,rows];return
        for value in [0,1]:yield from traces(ops+['push'],rows+[[value]],size+1,remaining-1)
        if size:yield from traces(ops+['pop'],rows+[[]],size-1,remaining-1)
    yield from traces(['FreqStack'],[[]],0,6)
    for n in [1,9,55,220,1000]:
        for mask in range(1,32):yield 902,[[str(x) for i,x in enumerate([1,2,3,7,9]) if mask>>i&1],n]
    for left,right in [(1,2),(4,1000),(1,1000000),(121,121),(484,484),(9,9)]+[(rng.randrange(1,10000),rng.randrange(10000,1000000)) for _ in range(20)]:yield 906,[str(left),str(right)]
    for n in range(1,5):
        for goal in range(n,7):
            for k in range(n):yield 920,[n,goal,k]
    for n in range(3,10):
        for bits in product(range(2),repeat=n):yield 927,[list(bits)]
    for n in range(1,8):yield 932,[n]
    for _ in range(90):yield 952,[rng.sample(range(1,51),rng.randint(1,10))]
    for _ in range(100):
        n=rng.randint(1,5);w=rng.randint(1,8);yield 960,[[''.join(rng.choice('abcd') for _ in range(w)) for _ in range(n)]]

def boundary_cases():
    # (ID,args,expected,proof). No brute-force oracle is called here.
    yield 827,[[[1]*500 for _ in range(500)]],250000,'All cells already form one island.'
    yield 827,[[[(r+c)%2 for c in range(500)] for r in range(500)]],5,'Every one is isolated; an interior zero joins exactly four ones.'
    yield 828,['A'*100000],100000,'Exactly the length-one substrings contribute one.'
    yield 847,[[[j for j in range(12) if i!=j] for i in range(12)]],11,'Any 12-vertex visit needs 11 edges; complete graph attains it.'
    yield 847,[[list(range(1,12))]+[[0] for _ in range(11)]],20,'A star walk starts and ends at leaves; nine internal leaves each require two edges, endpoints one each.'
    yield 851,[[[a,b] for a in range(500) for b in range(a+1,500)],list(range(500))],[0]*500,'Person zero is quieter and richer than everyone.'
    yield 854,['a'*10+'b'*10,'b'*10+'a'*10],10,'Twenty mismatches require at least ten swaps, attained by pairing opposing mismatches.'
    yield 862,[[100000]*100000,10**9],10000,'A length L interval sums to L*100000.'
    yield 862,[[-100000]*100000,10**9],-1,'Every nonempty interval is negative.'
    yield 864,[['@abcdefABCDEF'+'.'*17]+['#'*30]*29],6,'The sixth key lies six steps along the sole accessible corridor; locks are beyond all keys.'
    def chain(n,v):
        t=None
        for _ in range(n):t=[v,t,None]
        return t
    yield 872,[chain(200,200),chain(200,200)],True,'Each maximum-node tree has one leaf of value 200.'
    edges=[[0,b,10000] for b in range(1,3000)]
    for a in range(1,3000):
        for b in range(a+1,3000):
            if len(edges)==10000:break
            edges.append([a,b,10000])
        if len(edges)==10000:break
    yield 882,[edges,10**9,3000],100003000,'The connected star reaches every original vertex within 10001 moves; all 10000 subdivisions per each of 10000 edges lie within 30003 moves.'
    yield 882,[[[0,1,10000]],0,3000],1,'Zero moves reaches exactly the start, including disconnected maximum n.'
    yield 894,[20],[], 'Even node count cannot form a full binary tree.'
    yield 894,[19],None,'Independently check full structure, distinct shapes, 19 nodes, and Catalan(9)=4862 trees.'
    yield 895,[['FreqStack']+['push']*10000+['pop']*10000,[[]]+[[10**9]]*10000+[[]]*10000],[None]*10001+[10**9]*10000,'Exactly 20000 legal calls and maximum value; every popped value is identical.'
    yield 902,[list('123456789'),10**9],sum(9**i for i in range(1,10)),'All lengths one through nine are legal; 10-digit maximum contains forbidden zero.'
    yield 906,['999999999999999999','999999999999999999'],0,'Maximum endpoint lies strictly between 999999999^2 and 1000000000^2.'
    import math
    yield 920,[100,100,99],math.factorial(100)%1000000007,'Every song appears exactly once; all permutations satisfy cooldown.'
    yield 920,[100,100,0],math.factorial(100)%1000000007,'At equal song/playlist sizes, all songs once forces a permutation.'
    yield 927,[[0]*30000],None,'Any three nonempty zero blocks represent zero; validate witness directly.'
    yield 927,[[1]+[0]*29999],[-1,-1],'One total one cannot be split equally among three nonempty equal-valued parts.'
    yield 932,[1000],None,'Validate complete permutation and the forbidden-triple relation by independent positions.'
    yield 952,[[2*i for i in range(1,20000)]+[100000]],20000,'Maximum number of distinct values, including maximum value; all share factor two.'
    yield 960,[['z'*100]*100],0,'All maximum-width rows are already nondecreasing.'
    yield 960,[['z'*50+'a'*50]*100],50,'No kept z can precede a kept a; each constant block of length 50 is feasible.'
