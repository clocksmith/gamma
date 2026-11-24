import sys
input = sys.stdin.readline

from collections import deque

n,m = map(int, input().split())
qp = [tuple(map(int, input().split())) for _ in range(m)]

qp.sort(key=lambda x:x[1])

qp = deque(qp)

ans = 0
pre = 0

while qp:
    a,b = qp.popleft()
    if pre<a:
        ans += 1
        pre = b-1
print(ans)