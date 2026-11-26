import heapq
INF = float('inf')


def dijkstra(s, n, edges, d):
    d = [INF] * n
    d[s] = 0
    pq = [(0, s)]
    while len(pq):
        c, v = heapq.heappop(pq)
        if d[v] < c:
            continue
        for v2nvcost, nv in edges[v]:
            if c + v2nvcost < d[nv]:
                d[nv] = c + v2nvcost
                heapq.heappush(pq, (d[nv], nv))
    return d


n, m, s, t = map(int, input().split())
s -= 1
t -= 1
edges_yen = [[] for _ in range(n)]
edges_snuuk = [[] for _ in range(n)]
for _ in range(m):
    u, v, a, b = map(int, input().split())
    u -= 1
    v -= 1
    edges_yen[u].append((a, v))
    edges_yen[v].append((a, u))
    edges_snuuk[u].append((b, v))
    edges_snuuk[v].append((b, u))
d = [INF] * n
d_yen = dijkstra(s, n, edges_yen, d)
d = [INF] * n
d_snuuk = dijkstra(t, n, edges_snuuk, d)
temp = [0] * n  # 場所iで両替した時の最終スヌーク
for i in range(n):
    temp[i] = 10**15 - (d_yen[i] + d_snuuk[i])

ans = [INF] * n
ans[-1] = temp[-1]
for i in range(n - 2, -1, -1):
    ans[i] = max(ans[i + 1], temp[i])
# print(d_yen)
# print(d_snuuk)
for i in range(n):
    print(ans[i])
