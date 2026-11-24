import sys
from collections import deque

sr = lambda: sys.stdin.readline().rstrip()
ir = lambda: int(sr())
lr = lambda: list(map(int, sr().split()))

#1回ずつ数えて答えを3で割る
N, M = lr()
graph = [[] for _ in range(N+1)] # 1-indexed
for _ in range(M):
    u, v = lr()
    graph[u].append(v)

S, T = lr()
que = deque([(S, 0)])
time_set = [set() for _ in range(N+1)] # 1-indexed
while que:
    q, time = que.popleft()
    if time > M * 3:
        break
    for next in graph[q]:
        if (time+1) % 3 in time_set[next]:
            continue
        if next == T and (time+1) % 3 == 0:
            print((time+1)//3); exit()
        que.append((next, time+1))
        time_set[next].add((time+1)%3)

print(-1); exit()
# 52