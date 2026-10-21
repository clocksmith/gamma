"""Small-domain independent oracles for twenty additional development problems."""
from functools import lru_cache
import math
import random


def oracle(i, args):
    x = args[0]
    if i == 3:
        return max((b-a for a in range(len(x)+1) for b in range(a,len(x)+1) if len(set(x[a:b]))==b-a),default=0)
    if i == 4:
        s=sorted(x+args[1]);n=len(s);return (s[(n-1)//2]+s[n//2])/2
    if i == 7:
        v=int(str(abs(x))[::-1])*(-1 if x<0 else 1);return v if -2**31<=v<2**31 else 0
    if i == 9:return str(x)==str(x)[::-1]
    if i == 11:return max((min(x[a],x[b])*(b-a) for a in range(len(x)) for b in range(a+1,len(x))),default=0)
    if i == 14:
        out=''
        for chars in zip(*x):
            if len(set(chars))!=1:break
            out+=chars[0]
        return out
    if i == 20:
        prior=None
        while prior!=x:prior=x;x=x.replace('()','').replace('[]','').replace('{}','')
        return not x
    if i == 28:return x.find(args[1])
    if i == 34:
        matches=[k for k,v in enumerate(x) if v==args[1]]
        return [matches[0],matches[-1]] if matches else [-1,-1]
    if i == 35:return sum(v<args[1] for v in x)
    if i == 42:return sum(max(0,min(max(x[:k+1]),max(x[k:]))-v) for k,v in enumerate(x))
    if i == 53:return max(sum(x[a:b]) for a in range(len(x)) for b in range(a+1,len(x)+1))
    if i == 55:
        reach={0}
        for k in range(len(x)):
            if k in reach:reach.update(range(k+1,min(len(x),k+x[k]+1)))
        return len(x)-1 in reach
    if i == 58:return len(x.split()[-1])
    if i == 62:return math.comb(x+args[1]-2,x-1)
    if i == 64:
        @lru_cache(None)
        def f(a,b):
            if a==len(x)-1 and b==len(x[0])-1:return x[a][b]
            return x[a][b]+min([f(a+1,b)] if b==len(x[0])-1 else [f(a,b+1)] if a==len(x)-1 else [f(a+1,b),f(a,b+1)])
        return f(0,0)
    if i == 67:return bin(int(x,2)+int(args[1],2))[2:]
    if i == 69:return math.isqrt(x)
    if i == 70:return sum(math.comb(x-k,k) for k in range(x//2+1))
    if i == 1046:
        s=list(x)
        while len(s)>1:
            s.sort();a=s.pop();b=s.pop()
            if a!=b:s.append(a-b)
        return s[0] if s else 0
    raise ValueError(i)


def make_cases(i):
    r=random.Random(20261020+i)
    words=lambda: ''.join(r.choice('abc') for _ in range(r.randrange(12)))
    arrays=lambda minimum=0:[r.randrange(-10,11) for _ in range(r.randrange(minimum,14))]
    cases=[]
    for _ in range(80):
        if i==3:args=[words()]
        elif i==4:args=[sorted(arrays()),sorted(arrays(1))]
        elif i in [7,9]:args=[r.randrange(-2**31,2**31)]
        elif i in [11,42,55,1046]:args=[[r.randrange(1 if i==1046 else 0,12) for _ in range(r.randrange(2 if i==11 else 1,16))]]
        elif i==14:args=[[words() for _ in range(r.randrange(1,8))]]
        elif i==20:args=[''.join(r.choice('()[]{}') for _ in range(r.randrange(1,16)))]
        elif i==28:args=[words() or 'a',words() or 'a']
        elif i==34:args=[sorted(arrays()),r.randrange(-12,13)]
        elif i==35:args=[sorted(set(arrays(1))),r.randrange(-12,13)]
        elif i==53:args=[arrays(1)]
        elif i==58:args=[' '*r.randrange(4)+' '.join(words() or 'a' for _ in range(r.randrange(1,7)))+' '*r.randrange(4)]
        elif i==62:args=[r.randrange(1,12),r.randrange(1,12)]
        elif i==64:
            a,b=r.randrange(1,6),r.randrange(1,6);args=[[[r.randrange(10) for _ in range(b)] for _ in range(a)]]
        elif i==67:args=[bin(r.randrange(2**40))[2:],bin(r.randrange(2**40))[2:]]
        elif i==69:args=[r.randrange(2**31)]
        elif i==70:args=[r.randrange(1,46)]
        else:raise ValueError(i)
        cases.append({'args':args,'expected':oracle(i,args)})
    boundaries={3:[[''],['aaaa'],['abcabcbb']],4:[[[1],[]],[[],[1]],[[1,2],[3,4]]],7:[[0],[120],[-120],[1534236469],[-2**31]],9:[[0],[121],[-121],[10]],11:[[[0,0]],[[1,8,6,2,5,4,8,3,7]]],14:[[['']], [['same','same']], [['flower','flow','flight']]],20:[['()'],['([]{})'],['([)]']],28:[['abc','abc'],['a','aa']],34:[[[],1],[[1,1,1],1]],35:[[[1],0],[[1],2]],42:[[[0]],[[4,2,0,3,2,5]]],53:[[[-10]],[[-3,-2,-5]]],55:[[[0]],[[3,2,1,0,4]]],58:[[' a ']],62:[[1,1],[1,100]],64:[[[[0]]],[[[1,2],[3,4]]]],67:[['0','0'],['1'*128,'1']],69:[[0],[1],[2],[4],[2**31-1]],70:[[1],[2],[45]],1046:[[[1]],[[2,7,4,1,8,1]],[[1,1]]]}
    for args in boundaries[i]:cases.append({'args':args,'expected':oracle(i,args)})
    return cases
