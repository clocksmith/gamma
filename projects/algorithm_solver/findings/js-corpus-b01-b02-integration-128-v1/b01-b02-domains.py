"""Published input restrictions, applied before looking at execution outcomes."""
import math

def reasons(n,args):
    bad=[]
    def require(ok,label):
        if not ok:bad.append(label)
    integer=lambda x:type(x) is int
    if n==1:
        a,t=args;require(2<=len(a)<=10000,'length');require(all(integer(v) and abs(v)<=10**9 for v in a) and integer(t) and abs(t)<=10**9,'integer bounds')
        counts={};pairs=0
        for v in a:pairs+=counts.get(t-v,0);counts[v]=counts.get(v,0)+1
        require(pairs==1,'exactly one index pair')
    elif n==17:
        s,=args;require(isinstance(s,str) and len(s)<=4,'string length 0..4');require(all(c in '23456789' for c in s),'digits 2..9')
    elif n==33:
        a,t=args;require(1<=len(a)<=5000,'length');require(all(integer(v) and abs(v)<=10000 for v in a) and integer(t) and abs(t)<=10000,'integer bounds');require(len(set(a))==len(a),'distinct values');require(not a or sum(a[i]>a[(i+1)%len(a)] for i in range(len(a)))<=1,'rotation of ascending array')
    elif n==39:
        a,t=args;require(1<=len(a)<=30,'length');require(all(integer(v) and 2<=v<=40 for v in a),'positive values 2..40');require(len(set(a))==len(a),'distinct values');require(integer(t) and 1<=t<=40,'target 1..40')
    elif n==45:
        a,=args;require(1<=len(a)<=10000,'length');require(all(integer(v) and 0<=v<=1000 for v in a),'nonnegative values 0..1000');reach=0
        for i,v in enumerate(a):
            if i>reach:break
            reach=max(reach,i+v)
        require(reach>=len(a)-1,'last index reachable')
    elif n==50:
        x,e=args;require(type(x) in (int,float) and math.isfinite(x) and -100<x<100,'base bounds');require(integer(e) and -2**31<=e<=2**31-1,'signed32 exponent');require(x!=0 or e>0,'nonzero base or positive exponent')
        # Outcome-independent mathematical bound, no frozen expected consulted.
        magnitude_log=(e*math.log(abs(x))) if x else -math.inf
        require(magnitude_log<=math.log(10000)+1e-12,'mathematical result magnitude <=10000')
    else:raise ValueError('Unreviewed domain')
    return bad
