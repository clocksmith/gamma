"""3515. Shortest Path in a Weighted Tree.

Euler intervals turn edge-weight changes into subtree range additions and root-distance point queries; O(n+q log n) time and O(n+q) space. Inputs are preserved.
"""

def solve(n: int, edges: list[list[int]], queries: list[list[int]]) -> list[int]:
    graph = [[] for _ in range(n + 1)]
    for first, second, weight in edges:
        graph[first].append((second, weight))
        graph[second].append((first, weight))
    parent, edge_weight, distance, entry, leave = ([0] * (n + 1) for _ in range(5))
    timer = 0
    stack = [(1, 0, 0, False)]
    while stack:
        node, predecessor, weight, exiting = stack.pop()
        if exiting:
            leave[node] = timer
            continue
        parent[node] = predecessor
        edge_weight[node] = weight
        distance[node] = distance[predecessor] + weight
        entry[node] = timer
        timer += 1
        stack.append((node, predecessor, weight, True))
        for child, child_weight in graph[node]:
            if child != predecessor:
                stack.append((child, node, child_weight, False))
    changes = [0] * (n + 1)

    def add(index, amount):
        index += 1
        while index <= n:
            changes[index] += amount
            index += index & -index

    answers = []
    for query in queries:
        if query[0] == 1:
            _, first, second, weight = query
            child = first if parent[first] == second else second
            difference = weight - edge_weight[child]
            edge_weight[child] = weight
            add(entry[child], difference)
            add(leave[child], -difference)
        else:
            node = query[1]
            index, answer = entry[node] + 1, distance[node]
            while index:
                answer += changes[index]
                index -= index & -index
            answers.append(answer)
    return answers


class Solution:
    def treeQueries(self, n: int, edges: list[list[int]], queries: list[list[int]]) -> list[int]:
        return solve(n, edges, queries)
