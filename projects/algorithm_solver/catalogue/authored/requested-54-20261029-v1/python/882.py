"""Original development candidate; independent qualification pending."""
def solve(edges, maxMoves, n):
    graph = [[] for _ in range(n)]
    for u,v,c in edges:
        graph[u].append((v,c+1))
        graph[v].append((u,c+1))
    distance = [float('inf')]*n
    distance[0] = 0
    used = [False]*n
    for _ in range(n):
        u = min((i for i in range(n) if not used[i]), key=lambda i: distance[i], default=-1)
        if u == -1 or distance[u] > maxMoves:
            break
        used[u] = True
        for v,w in graph[u]:
            distance[v] = min(distance[v],distance[u]+w)
    result = sum(d <= maxMoves for d in distance)
    for u,v,c in edges:
        result += min(c,max(0,maxMoves-distance[u])+max(0,maxMoves-distance[v]))
    return result


class Solution:
    def reachableNodes(self, edges, maxMoves, n):
        return solve(edges, maxMoves, n)
