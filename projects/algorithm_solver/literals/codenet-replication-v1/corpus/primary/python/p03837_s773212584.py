import itertools

N,M = list(map(int,input().split(" ")))

# graph = [list(map(int,input().split(" "))) for _  in range(M)]
used = [False] * M
INF = 10**20
cost = [[INF for _ in range(N+1)] for _ in range(N+1)]
edges = []
for i in range(M):
    a,b,c = list(map(int,input().split(" ")))
    cost[a][b] = c
    cost[b][a] = c
    edges.append((a,b,c))
for i in range(1,N+1):
    cost[i][i] = 0
for k in range(1,N+1):
    for i in range(1,N+1):
        for j in range(1,N+1):

            cost[i][j] = min(cost[i][j],cost[i][k] + cost[k][j])
            cost[j][i] = min(cost[j][i], cost[j][k] + cost[k][i])
ans = 0
for k,edge in enumerate(edges):
            a,b,c = edge
            if  cost[a][b] !=c:
                ans += 1
print(ans)
