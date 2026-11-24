import sys
readline = sys.stdin.readline
write = sys.stdout.write

M = 1000000
sq = int(M**.5)
pl = []
p = [1]*(M+1)
p[0] = p[1] = 0
for x in range(2, sq+1):
    if p[x]:
        for y in range(x*x, M+1, x):
            p[y] = 0
        pl.append(x)
for x in range(sq+1, M+1):
    if p[x]:
        pl.append(x)

def solve():
    N = int(readline())
    if N == 0:
        return False
    ans = 0
    N2 = N//2
    for x in pl:
        if N2 < x:
            break
        if p[N-x]:
            ans += 1
    write("%d\n" % ans)
    return True
while solve():
    ...
