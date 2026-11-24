def hoge(p):
    ret = {}
    pp = 2
    while pp * pp <= p:
        while p % pp == 0:
            ret[pp] = ret[pp]+1 if pp in ret else 1
            p //= pp
        pp += 1
    if p != 1: ret[p] = 1
    return ret

N,P=map(int,input().split())
if N==1:
    print(P)
elif P==1:
    print(1)
else:
    ans = 1
    ret = hoge(P)
    for p,e in ret.items():
        ans *= max(1, p**(e//N))
    print(ans)    
