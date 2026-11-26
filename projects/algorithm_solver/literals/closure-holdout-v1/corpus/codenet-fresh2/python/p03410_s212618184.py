from bisect import bisect_right as br
N = int(input())
A = [int(a) for a in input().split()]
B = [int(a) for a in input().split()]
s, t = 0, 0
for i in range(N):
    s ^= A[i]
    t ^= B[i]
ans = (s ^ t) * (N % 2)
for k in range(1, 29):
    m = (1<<k)
    AA = sorted([a % m for a in A])
    BB = sorted([a % m for a in B])[::-1]
    i, j = 0, 0
    while i < N and AA[i] + BB[j] < m:
        i += 1
    s = 0
    while i < N:
        while j < N and AA[i] + BB[j] >= m:
            j += 1
        s += j
        i += 1
    ans ^= (s % 2) << k
print(ans)