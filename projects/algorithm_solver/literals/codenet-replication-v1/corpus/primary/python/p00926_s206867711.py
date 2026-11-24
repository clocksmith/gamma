N, m = map(int, input().split())
v = [0]*N
for i in range(m):
    c, d = map(int, input().split())
    v[c-1] += 1
    v[d-1] -= 1
s = 0; fst = 0
ans = N+1
for i in range(N):
    if s == 0 and v[i] > 0:
        fst = i
    s += v[i]
    if s == 0 and v[i] < 0:
        ans += (i - fst)*2
print(ans)