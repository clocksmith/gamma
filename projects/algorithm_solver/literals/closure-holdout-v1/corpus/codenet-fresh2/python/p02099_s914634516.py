N = int(input())
P = {}
for i in range(N):
    p = float(input())
    P.setdefault(p, []).append(i)

ans = [0]*N
c = 0
for p, s in sorted(P.items()):
    for i in s:
        ans[i] = 3*c + len(s)-1
    c += len(s)
print(*ans, sep='\n')

