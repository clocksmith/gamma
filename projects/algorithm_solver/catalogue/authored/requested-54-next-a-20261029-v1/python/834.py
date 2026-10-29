"""Original development candidate; qualification unknown."""
def solve(n, edges):
    graph = [[] for _ in range(n)]
    for a,b in edges:
        graph[a].append(b)
        graph[b].append(a)
    parent = [-1]*n
    order = [0]
    for u in order:
        for v in graph[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)
    size = [1]*n
    answer = [0]*n
    for u in reversed(order[1:]):
        p = parent[u]
        size[p] += size[u]
        answer[p] += answer[u]+size[u]
    for u in order[1:]:
        answer[u] = answer[parent[u]]+n-2*size[u]
    return answer


class Solution:
    def sumOfDistancesInTree(self, n, edges):
        return solve(n, edges)
