"""1192. Critical Connections in a Network.

Iterative low-link DFS; O(n + m) time and space. Inputs are preserved.
"""

def solve(n: int, connections: list[list[int]]) -> list[list[int]]:
    graph = [[] for _ in range(n)]
    for edge, (first, second) in enumerate(connections):
        graph[first].append((second, edge))
        graph[second].append((first, edge))
    entered = [-1] * n
    low = [0] * n
    parent = [-1] * n
    parent_edge = [-1] * n
    offset = [0] * n
    bridges = []
    clock = 0
    for root in range(n):
        if entered[root] != -1:
            continue
        entered[root] = low[root] = clock
        clock += 1
        stack = [root]
        while stack:
            node = stack[-1]
            if offset[node] == len(graph[node]):
                stack.pop()
                previous = parent[node]
                if previous != -1:
                    if low[node] > entered[previous]:
                        bridges.append([previous, node])
                    low[previous] = min(low[previous], low[node])
                continue
            neighbor, edge = graph[node][offset[node]]
            offset[node] += 1
            if edge == parent_edge[node]:
                continue
            if entered[neighbor] != -1:
                low[node] = min(low[node], entered[neighbor])
                continue
            parent[neighbor] = node
            parent_edge[neighbor] = edge
            entered[neighbor] = low[neighbor] = clock
            clock += 1
            stack.append(neighbor)
    return bridges


class Solution:
    def criticalConnections(self, n: int, connections: list[list[int]]) -> list[list[int]]:
        return solve(n, connections)
