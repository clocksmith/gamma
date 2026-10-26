"""Definition-level oracles for the 67 imports without archived independent cases.

Written from the pinned statement-only snapshots, without reading the candidate
implementations. Small combinatorial cases use enumeration; large fixtures have
simple independently checkable structure. This module executes no candidates.
"""
from collections import Counter, deque
from functools import cache
from itertools import combinations, permutations, product
from math import gcd, prod
import random

IDS = (301, 1735, 1799, 1830, 2514, 2612, 2954, 2963, 3414, 3512, 3516, 3536,
       3541, 3545, 3550, 3560, 3582, 3591, 3602, 3606, 3622, 3633, 3637, 3643,
       3658, 3663, 3668, 3674, 3678, 3683, 3684, 3688, 3692, 3697, 3701, 3707,
       3712, 3718, 3726, 3731, 3736, 3740, 3745, 3750, 3754, 3769, 3774, 3783,
       3794, 3798, 3803, 3813, 3823, 3827, 3833, 3838, 3842, 3852, 3856, 3861,
       3866, 3870, 3875, 3880, 3884, 3940, 3945)
VOWELS = set('aeiou')
MOD = 10**9 + 7


def validate(pid, args):
    """Pinned statement-domain checks; bool is never accepted as an integer."""
    def integer(x, low, high):
        return type(x) is int and low <= x <= high
    def ints(xs, low, high, minimum=1, maximum=100):
        return type(xs) is list and minimum <= len(xs) <= maximum and all(integer(x, low, high) for x in xs)
    def text(s, alphabet, minimum=1, maximum=100):
        return type(s) is str and minimum <= len(s) <= maximum and set(s) <= set(alphabet)
    letters = 'abcdefghijklmnopqrstuvwxyz'
    if type(args) is not list or pid not in IDS:
        raise ValueError('unknown problem or unordered arguments')
    a = args
    scalars = {3536:(10,10**9),3602:(1,1000),3622:(1,10**6),3658:(1,1000),3663:(1,2**31-1),3697:(1,10**9),3726:(1,10**15),3750:(1,10**9),3754:(0,10**9),3783:(1,10**9),3827:(0,1000),3870:(1,10**5),3945:(1,10**9)}
    good = False
    try:
        if pid in scalars:
            good = len(a)==1 and integer(a[0],*scalars[pid])
        elif pid in (3541,3692,3803,3856,3884):
            good = len(a)==1 and text(a[0],letters)
        elif pid==3707:good=len(a)==1 and text(a[0],letters,2)
        elif pid==3798:good=len(a)==1 and text(a[0],'12')
        elif pid==3813:good=len(a)==1 and text(a[0],letters+' 0123456789')
        elif pid==3823:good=len(a)==1 and text(a[0],letters+'!@#$%^&*()')
        elif pid==3582:good=len(a)==1 and text(a[0],letters+letters.upper()+' ',1,150)
        elif pid==3545:good=len(a)==2 and text(a[0],letters,1,16) and integer(a[1],1,16)
        elif pid==3516:good=len(a)==3 and all(integer(x,1,100)for x in a)
        elif pid==3512:good=len(a)==2 and ints(a[0],1,1000,1,1000) and integer(a[1],1,100)
        elif pid==3550:good=len(a)==1 and ints(a[0],0,1000)
        elif pid==3591:good=len(a)==1 and ints(a[0],0,100)
        elif pid==3637:good=len(a)==1 and ints(a[0],-1000,1000,3)
        elif pid==3674:good=len(a)==1 and ints(a[0],1,10**5)
        elif pid==3678:good=len(a)==1 and ints(a[0],-100,100)
        elif pid in (3688,3701,3736,3833,3842,3852,3866):good=len(a)==1 and ints(a[0],1,100)
        elif pid==3769:good=len(a)==1 and ints(a[0],1,10**9)
        elif pid==3880:good=len(a)==1 and ints(a[0],0,2)
        elif pid==3740:good=len(a)==1 and ints(a[0],1,len(a[0]))
        elif pid==3745:good=len(a)==1 and ints(a[0],-100,100,3)
        elif pid in (3712,3718,3861):good=len(a)==2 and ints(a[0],1,100) and integer(a[1],1,100)
        elif pid in (3684,3774,3940):good=len(a)==2 and ints(a[0],1,10**9 if pid==3684 else 100) and integer(a[1],1,len(a[0])) and (pid!=3940 or a[0]==sorted(a[0]))
        elif pid==3731:good=len(a)==1 and ints(a[0],1,100,2) and len(set(a[0]))==len(a[0])
        elif pid==3875:good=len(a)==1 and ints(a[0],1,100) and len(set(a[0]))==len(a[0])
        elif pid==3794:good=len(a)==2 and text(a[0],letters) and integer(a[1],1,len(a[0]))
        elif pid==3560:
            n,m,k=a;good=integer(k,2,10**5) and integer(n,1,2*k) and integer(m,1,2*k) and (n+k-1)//k+(m+k-1)//k<=3
        elif pid==3606:
            codes,lines,active=a;n=len(codes);good=all(type(xs)is list for xs in (codes,lines,active)) and 1<=n<=100 and len(lines)==len(active)==n and all(type(s)is str and len(s)<=100 and all(32<=ord(c)<=126 for c in s)for s in codes+lines) and all(type(x)is bool for x in active)
        elif pid==3633:good=len(a)==4 and all(ints(xs,1,1000)for xs in a) and len(a[0])==len(a[1]) and len(a[2])==len(a[3])
        elif pid==3643:
            grid,x,y,k=a;m=len(grid);n=len(grid[0]);good=type(grid)is list and 1<=m<=50 and 1<=n<=50 and all(ints(row,1,100,n,n)for row in grid) and integer(x,0,m-1) and integer(y,0,n-1) and integer(k,1,min(m-x,n-y))
        elif pid==3668:
            order,friends=a;n=len(order);good=ints(order,1,n) and sorted(order)==list(range(1,n+1)) and ints(friends,1,n,1,min(8,n)) and friends==sorted(set(friends))
        elif pid==3683:good=len(a)==1 and type(a[0])is list and 1<=len(a[0])<=100 and all(ints(row,1,100,2,2)for row in a[0])
        elif pid==3838:good=len(a)==2 and type(a[0])is list and 1<=len(a[0])<=100 and all(text(w,letters,1,10)for w in a[0]) and ints(a[1],1,100,26,26)
        elif pid==301:good=len(a)==1 and text(a[0],letters+'()',1,25) and sum(c in'()'for c in a[0])<=20
        elif pid==1735:good=len(a)==1 and type(a[0])is list and 1<=len(a[0])<=10000 and all(ints(row,1,10000,2,2)for row in a[0])
        elif pid==1799:good=len(a)==1 and ints(a[0],1,10**6,2,14) and len(a[0])%2==0
        elif pid==1830:good=len(a)==1 and text(a[0],letters,1,3000)
        elif pid==2514:good=len(a)==1 and text(a[0],letters+' ',1,100000) and all(a[0].split(' '))
        elif pid==2612:
            n,p,banned,k=a;good=integer(n,1,100000) and integer(p,0,n-1) and ints(banned,0,n-1,0,n-1) and len(set(banned))==len(banned) and p not in banned and integer(k,1,n)
        elif pid==2954:
            n,sick=a;good=integer(n,2,100000) and ints(sick,0,n-1,1,n-1) and sick==sorted(set(sick))
        elif pid==2963:good=len(a)==1 and ints(a[0],1,10**9,1,100000)
        elif pid==3414:good=len(a)==1 and type(a[0])is list and 1<=len(a[0])<=50000 and all(ints(row,1,10**9,3,3) and row[0]<=row[1]for row in a[0])
    except (TypeError, ValueError, IndexError, KeyError):
        good = False
    if not good:
        raise ValueError(f'{pid}: outside pinned statement domain')


def expected(pid, a):
    validate(pid, a)
    if pid == 301:
        s = a[0]
        layer = {s}
        while True:
            valid = []
            for t in layer:
                balance = 0
                for c in t:
                    balance += (c == '(') - (c == ')')
                    if balance < 0:
                        break
                else:
                    if balance == 0:
                        valid.append(t)
            if valid:
                return sorted(valid)
            layer = {t[:i] + t[i+1:] for t in layer for i, c in enumerate(t) if c in '()'}
    if pid == 1735:
        @cache
        def count(n, k):
            if k == 1:
                return 1
            if n == 1:
                return 1
            return sum(count(n-1, k//d) for d in range(1, k+1) if k % d == 0) % MOD
        return [count(n, k) for n, k in a[0]]
    if pid == 1799:
        xs = tuple(a[0])
        @cache
        def search(left):
            if not left:
                return 0
            step = (len(xs) - len(left)) // 2 + 1
            return max(step*gcd(left[i], left[j]) + search(tuple(x for k, x in enumerate(left) if k not in (i, j)))
                       for i in range(len(left)) for j in range(i+1, len(left)))
        return search(xs)
    if pid == 1830:
        s = a[0]
        if len(set(s)) == 1:
            return 0
        return sum(''.join(t) < s for t in set(permutations(s))) % MOD
    if pid == 2514:
        return prod(1 if len(set(w)) == 1 else len(set(permutations(w))) for w in a[0].split(' ')) % MOD
    if pid == 2612:
        n, p, banned, k = a
        distances = [-1] * n; distances[p] = 0; queue = deque([p]); blocked = set(banned)
        while queue:
            x = queue.popleft()
            for start in range(max(0, x-k+1), min(x, n-k)+1):
                y = 2*start+k-1-x
                if y not in blocked and distances[y] == -1:
                    distances[y] = distances[x]+1; queue.append(y)
        return distances
    if pid == 2954:
        n, sick = a
        if sick == [0] or sick == [n-1]:
            return 1
        @cache
        def count(infected):
            if len(infected) == n:
                return 1
            choices = {j for i in infected for j in (i-1, i+1) if 0 <= j < n and j not in infected}
            return sum(count(tuple(sorted((*infected, j)))) for j in choices) % MOD
        return count(tuple(sick))
    if pid == 2963:
        xs = a[0]
        if len(set(xs)) == 1:
            return 1
        answer = 0
        for mask in range(1 << (len(xs)-1)):
            blocks = []; start = 0
            for i in range(len(xs)-1):
                if mask >> i & 1:
                    blocks.append(set(xs[start:i+1])); start = i+1
            blocks.append(set(xs[start:]))
            answer += sum(map(len, blocks)) == len(set().union(*blocks))
        return answer % MOD
    if pid == 3414:
        xs = a[0]
        if len(xs) > 20 and all(x == xs[0] for x in xs):
            return [0]
        best = (0, [])
        for size in range(1, min(4, len(xs))+1):
            for indices in combinations(range(len(xs)), size):
                if any(max(xs[i][0], xs[j][0]) <= min(xs[i][1], xs[j][1]) for i, j in combinations(indices, 2)):
                    continue
                score = sum(xs[i][2] for i in indices)
                if score > best[0] or score == best[0] and list(indices) < best[1]:
                    best = (score, list(indices))
        return best[1]
    if pid == 3512:
        total, k = sum(a[0]), a[1]
        return next(i for i in range(k) if (total-i) % k == 0)
    if pid == 3516:
        x, y, z = a
        return 0 if abs(x-z) == abs(y-z) else 1 if abs(x-z) < abs(y-z) else 2
    if pid == 3536:
        return max(int(x)*int(y) for x, y in combinations(str(a[0]), 2))
    if pid == 3541:
        counts = Counter(a[0])
        return max([v for k, v in counts.items() if k in VOWELS] or [0]) + max([v for k, v in counts.items() if k not in VOWELS] or [0])
    if pid == 3545:
        s, k = a; counts = Counter(s)
        return min(len(s)-sum(counts[c] for c in choice) for choice in combinations(counts, min(k, len(counts))))
    if pid == 3550:
        return next((i for i, n in enumerate(a[0]) if sum(map(int, str(n))) == i), -1)
    if pid == 3560:
        n, m, k = a
        if max(n, m) <= k:
            return 0
        length = max(n, m)
        return min(x*(length-x) for x in range(1, length) if max(x, length-x) <= k)
    if pid == 3582:
        words = a[0].lower().split()
        return ('#' + ''.join(w if i == 0 else w[0].upper()+w[1:] for i, w in enumerate(words)))[:100]
    if pid == 3591:
        return any(n > 1 and all(n % d for d in range(2, n)) for n in Counter(a[0]).values())
    if pid == 3602:
        n = a[0]; value = n**3; digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'; out = ''
        while value:
            value, r = divmod(value, 36); out = digits[r]+out
        return format(n*n, 'X')+out
    if pid == 3606:
        categories = ['electronics', 'grocery', 'pharmacy', 'restaurant']
        allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
        valid = [(categories.index(b), c) for c, b, active in zip(*a) if active and b in categories and c and set(c) <= allowed]
        return [c for _, c in sorted(valid)]
    if pid == 3622:
        digits = list(map(int, str(a[0])))
        return a[0] % (sum(digits)+prod(digits)) == 0
    if pid == 3633:
        ls, ld, ws, wd = a
        return min(min(max(l+d, w)+e, max(w+e, l)+d) for l, d in zip(ls, ld) for w, e in zip(ws, wd))
    if pid == 3637:
        xs = a[0]
        return any(all(xs[i] < xs[i+1] for i in range(p)) and all(xs[i] > xs[i+1] for i in range(p, q)) and all(xs[i] < xs[i+1] for i in range(q, len(xs)-1)) for p in range(1, len(xs)-2) for q in range(p+1, len(xs)-1))
    if pid == 3643:
        grid, x, y, k = a
        return [[grid[2*x+k-1-i][j] if x <= i < x+k and y <= j < y+k else v for j, v in enumerate(row)] for i, row in enumerate(grid)]
    if pid == 3658:
        return gcd(sum(range(1, 2*a[0]+1, 2)), sum(range(2, 2*a[0]+1, 2)))
    if pid == 3663:
        s = str(a[0]); return int(min(set(s), key=lambda d: (s.count(d), d)))
    if pid == 3668:
        return sorted(a[1], key=a[0].index)
    if pid == 3674:
        # One operation on the whole array always suffices; zero iff already equal.
        return int(any(x != a[0][0] for x in a[0]))
    if pid == 3678:
        xs = a[0]; return next(n for n in range(1, 10000) if n not in xs and n*len(xs) > sum(xs))
    if pid == 3683:
        return min(s+t for s, t in a[0])
    if pid == 3684:
        return sorted(set(a[0]), reverse=True)[:a[1]]
    if pid == 3688:
        result = 0
        for n in a[0]:
            if n % 2 == 0:
                result |= n
        return result
    if pid == 3692:
        counts = Counter(a[0]); groups = {n: sorted(c for c, v in counts.items() if v == n) for n in counts.values()}
        return ''.join(groups[max(groups, key=lambda n: (len(groups[n]), n))])
    if pid == 3697:
        s = str(a[0]); return [int(c)*10**i for i, c in reversed(list(enumerate(reversed(s)))) if c != '0']
    if pid == 3701:
        return sum(a[0][::2])-sum(a[0][1::2])
    if pid == 3707:
        s = a[0]; values = [ord(c)-96 for c in s]
        return any(sum(values[:i]) == sum(values[i:]) for i in range(1, len(s)))
    if pid == 3712:
        xs, k = a; return sum(x for x in xs if xs.count(x) % k == 0)
    if pid == 3718:
        xs, k = a; return next(x*k for x in range(1, len(xs)+2) if x*k not in xs)
    if pid == 3726:
        return int(''.join(c for c in str(a[0]) if c != '0'))
    if pid == 3731:
        return sorted(set(range(min(a[0]), max(a[0])+1))-set(a[0]))
    if pid == 3736:
        return sum(max(a[0])-x for x in a[0])
    if pid == 3740:
        xs = a[0]
        return min([abs(i-j)+abs(j-k)+abs(k-i) for i, j, k in combinations(range(len(xs)), 3) if xs[i] == xs[j] == xs[k]] or [-1])
    if pid == 3745:
        return max(x+y-z for x, y, z in permutations(a[0], 3))
    if pid == 3750:
        s = bin(a[0])[2:]; return sum(x != y for x, y in zip(s, reversed(s)))
    if pid == 3754:
        s = ''.join(c for c in str(a[0]) if c != '0'); return int(s or '0')*sum(map(int, s))
    if pid == 3769:
        return sorted(a[0], key=lambda n: (int(bin(n)[2:][::-1], 2), n))
    if pid == 3774:
        xs, k = a; return abs(sum(sorted(xs)[-k:])-sum(sorted(xs)[:k]))
    if pid == 3783:
        return abs(a[0]-int(str(a[0])[::-1]))
    if pid == 3794:
        return a[0][:a[1]][::-1]+a[0][a[1]:]
    if pid == 3798:
        return max([a[0][:i+1] for i, c in enumerate(a[0]) if c == '2'] or [''], key=lambda s: (len(s), s))
    if pid == 3803:
        return sum(len(set(a[0][:i])) == i % 3 for i in range(1, len(a[0])+1))
    if pid == 3813:
        v = sum(c in VOWELS for c in a[0]); c = sum('a' <= c <= 'z' and c not in VOWELS for c in a[0])
        return v//c if c else 0
    if pid == 3823:
        s = a[0]; letters = iter(reversed([c for c in s if 'a' <= c <= 'z'])); special = iter(reversed([c for c in s if not 'a' <= c <= 'z']))
        return ''.join(next(letters) if 'a' <= c <= 'z' else next(special) for c in s)
    if pid == 3827:
        return sum(len(set(bin(x)[2:])) == 1 for x in range(a[0]+1))
    if pid == 3833:
        xs = a[0]; return sum(xs[i]*(len(xs)-i-1) > sum(xs[i+1:]) for i in range(len(xs)-1))
    if pid == 3838:
        return ''.join(chr(122-sum(a[1][ord(c)-97] for c in w) % 26) for w in a[0])
    if pid == 3842:
        return sorted(n for n in set(a[0]) if a[0].count(n) % 2)
    if pid == 3852:
        xs = a[0]; return list(min([(x, y) for x, y in combinations(sorted(set(xs)), 2) if xs.count(x) != xs.count(y)] or [(-1, -1)]))
    if pid == 3856:
        return a[0].rstrip('aeiou')
    if pid == 3861:
        sizes, target = a; return min([i for i, n in enumerate(sizes) if n >= target], key=lambda i: (sizes[i], i), default=-1)
    if pid == 3866:
        return next((n for n in a[0] if n % 2 == 0 and a[0].count(n) == 1), -1)
    if pid == 3870:
        return sum(format(n, ',').count(',') for n in range(1, a[0]+1))
    if pid == 3875:
        xs = a[0]; options = [{x % 2} | {(x-y) % 2 for j, y in enumerate(xs) if i != j} for i, x in enumerate(xs)]
        return any(all(p in option for option in options) for p in (0, 1))
    if pid == 3880:
        return min([abs(i-j) for i, x in enumerate(a[0]) for j, y in enumerate(a[0]) if x == 1 and y == 2] or [-1])
    if pid == 3884:
        return next((i for i, c in enumerate(a[0]) if c == a[0][-i-1]), -1)
    if pid == 3940:
        return [x for i, x in enumerate(a[0]) if a[0][:i+1].count(x) <= a[1]]
    if pid == 3945:
        return sum(map(int, str(a[0])))
    raise ValueError('unknown fresh oracle')


def build():
    rng = random.Random(20261026)
    out = {pid: [] for pid in IDS}
    def add(pid, args):
        out[pid].append({'args': args, 'expected': expected(pid, args), 'compare': 'return'})
    # Bounded exhaustive integer inputs plus declared extremes.
    scalars = {3536:(10,10**9),3602:(1,1000),3622:(1,10**6),3658:(1,1000),3663:(1,2**31-1),
               3697:(1,10**9),3726:(1,10**15),3750:(1,10**9),3754:(0,10**9),3783:(1,10**9),
               3827:(0,1000),3870:(1,10**5),3945:(1,10**9)}
    for pid,(low,high) in scalars.items():
        for n in sorted(set(range(low,min(high,200)+1))|{high,high-1}|{rng.randint(low,high)for _ in range(30)}):add(pid,[n])
    strings = {3541:'aeiobcz',3545:'abcde',3582:' aABcD ',3692:'abcde',3707:'abcz',3798:'12',
               3803:'abc',3813:'aeiobc 012',3823:'abc!@#$%^&*()',3856:'abcdeiou',3884:'abc'}
    for pid,alphabet in strings.items():
        high = 16 if pid==3545 else 150 if pid==3582 else 100
        low = 2 if pid==3707 else 1
        for size in [low,high]+[rng.randint(low,min(high,15))for _ in range(160)]:
            s=''.join(rng.choice(alphabet)for _ in range(size));add(pid,[s,rng.randint(1,16)]if pid==3545 else[s])
    arrays = (3512,3550,3591,3637,3674,3678,3684,3688,3701,3712,3718,3736,3740,3745,3769,3774,3833,3842,3852,3861,3866,3880,3940)
    for pid in arrays:
        for trial in range(160):
            low = 3 if pid in (3637,3745) else 1
            size=100 if trial==0 and pid not in(3637,3740,3745)else rng.randint(low,10)
            lo,hi = (-5,5)if pid in(3637,3678,3745)else(0,2)if pid==3880 else(0,20)if pid in(3550,3591)else(1,size)if pid==3740 else(1,20)
            xs=[rng.randint(lo,hi)for _ in range(size)]
            if pid==3940:xs.sort()
            args=[xs]
            if pid in (3512,3712,3718,3861):args.append(rng.randint(1,100))
            if pid in (3684,3774,3940):args.append(rng.randint(1,size))
            add(pid,args)
    for _ in range(160):
        add(3516,[rng.randint(1,100)for _ in range(3)])
        k=rng.randint(2,50);n=rng.randint(1,2*k);m=rng.randint(1,k);add(3560,[n,m,k]);add(3560,[m,n,k])
        codes=[rng.choice(['','a','Z','A','_','a-b','a1',' ', '@','aa'])for _ in range(8)]
        add(3606,[codes,[rng.choice(['electronics','grocery','pharmacy','restaurant','bad',''])for _ in codes],[bool(rng.randrange(2))for _ in codes]])
        n,m=rng.randint(1,8),rng.randint(1,8);add(3633,[[rng.randint(1,1000)for _ in range(z)]for z in(n,n,m,m)])
        m,n=rng.randint(1,8),rng.randint(1,8);k=rng.randint(1,min(m,n));add(3643,[[[rng.randint(1,100)for _ in range(n)]for _ in range(m)],rng.randint(0,m-k),rng.randint(0,n-k),k])
        order=list(range(1,rng.randint(1,20)+1));rng.shuffle(order);add(3668,[order,sorted(rng.sample(order,rng.randint(1,min(8,len(order)))))])
        add(3683,[[[rng.randint(1,100),rng.randint(1,100)]for _ in range(rng.randint(1,10))]])
        add(3731,[rng.sample(range(1,101),rng.randint(2,100))])
        s=''.join(rng.choice('abcz')for _ in range(rng.randint(1,100)));add(3794,[s,rng.randint(1,len(s))])
        add(3838,[[''.join(rng.choice('abcz')for _ in range(rng.randint(1,10)))for _ in range(rng.randint(1,10))],[rng.randint(1,100)for _ in range(26)]])
        add(3875,[rng.sample(range(1,101),rng.randint(1,100))])
    for size in range(1,7):
        for xs in product('()a',repeat=size):
            if size<=4 or rng.random()<0.05:add(301,[''.join(xs)])
        for _ in range(35):
            add(1830,[''.join(rng.choice('abc')for _ in range(size))])
            add(2514,[' '.join(''.join(rng.choice('abc')for _ in range(rng.randint(1,6)))for _ in range(rng.randint(1,3)))])
            add(2963,[[rng.randint(1,3)for _ in range(size)]])
    for _ in range(120):
        add(1735,[[[rng.randint(1,5),rng.randint(1,30)]for _ in range(5)]])
        add(1799,[[rng.randint(1,12)for _ in range(2*rng.randint(1,4))]])
        n=rng.randint(2,8);sick=sorted(rng.sample(range(n),rng.randint(1,n-1)));add(2954,[n,sick])
        n=rng.randint(1,12);p=rng.randrange(n);banned=rng.sample([i for i in range(n)if i!=p],rng.randrange(n));add(2612,[n,p,banned,rng.randint(1,n)])
        intervals=[]
        for _ in range(rng.randint(1,10)):
            lo=rng.randint(1,10);intervals.append([lo,rng.randint(lo,12),rng.randint(1,10)])
        add(3414,[intervals])
    add(1735,[[[10000,1]]*10000]);add(1799,[[1]*14]);add(1830,['a'*3000]);add(2514,['a'*100000])
    add(2612,[100000,0,[],1]);add(2954,[100000,[0]]);add(2963,[[1]*100000])
    # Separate maximum dimension and maximum values to fit the unchanged wire cap.
    # Their simultaneous maximum is not claimed as an executed fixture.
    add(3414,[[[1,1,1]]*50000]);add(3414,[[[1,10**9,10**9]]])
    return out
