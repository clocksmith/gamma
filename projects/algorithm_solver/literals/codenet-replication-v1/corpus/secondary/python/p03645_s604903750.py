import sys
input = sys.stdin.readline
N, M = map(int, input().split())
ship = [[] for i in range(N+1)]

for i in range(M):
    a, b = map(int, input().split())
    ship[a].append(b)
    ship[b].append(a)

flag = 0
for i in ship[1]:
    if N in ship[i]:
        flag = 1
if flag == 1:
    print("POSSIBLE")
else:
    print("IMPOSSIBLE")
