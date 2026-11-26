N = int(input())
A = list(map(int,input().split()))
from collections import Counter
from bisect import bisect
vs = list(Counter(A).values())
vs.sort()
cums = [0]
for v in vs:
    cums.append(cums[-1] + v)

def is_ok(k,m):
    j = bisect(vs,m)
    z = cums[j] + m*(len(vs)-j)
    return z >= m*k

ans = []
for k in range(1,N+1):
    if k > len(vs):
        ans.append(0)
    else:
        ok = 0
        ng = N//k + 1
        while ng-ok > 1:
            m = (ok+ng)//2
            if is_ok(k,m):
                ok = m
            else:
                ng = m
        ans.append(ok)

print(*ans, sep='\n')