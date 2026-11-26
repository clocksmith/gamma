import heapq

def dijkstra_heap(s):
    d = [float('inf')] * n
    used = [True] * n
    d[s] = 0
    used[s] = False
    edgelist = []
    for e in edge[s]:
        heapq.heappush(edgelist, e)
    while len(edgelist):
        minedge = heapq.heappop(edgelist)
        if not used[minedge[1]]:
            continue
        v = minedge[1]
        d[v] = minedge[0]
        used[v] = False
        for e in edge[v]:
            if used[e[1]]:
                heapq.heappush(edgelist, [e[0]+d[v], e[1]])
    return d

n,e,r = map(int, input().split())
std = [[int(x) for x in input().split()] for _ in range(e)]
edge = [[] for _ in range(n)]
for s, t, d in std:
    edge[s].append([d, t])
ans = dijkstra_heap(r)
for x in ans:
    if x==float('inf'): print('INF')
    else: print(x)

