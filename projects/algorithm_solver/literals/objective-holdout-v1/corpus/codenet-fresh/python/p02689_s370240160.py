import sys
input = lambda: sys.stdin.readline().rstrip()

n, m = map(int, input().split())
h = list(map(int, input().split()))
max_h = [0 for _ in range(n)]
for i in range(m):
    a, b = map(int, input().split())
    a -= 1
    b -= 1
    max_h[a] = max(max_h[a], h[b])
    max_h[b] = max(max_h[b], h[a])

cnt = 0
for i in range(n):
    if max_h[i] < h[i]:
        cnt += 1
print(cnt)