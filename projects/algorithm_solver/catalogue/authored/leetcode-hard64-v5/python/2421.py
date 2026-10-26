"""2421. Number of Good Paths. Activate equal-value groups and count endpoints within union-find components."""


def solve(vals: list[int], edges: list[list[int]]) -> int:
    """O(n log n) time and O(n) space for a tree. Inputs are preserved."""
    size = len(vals)
    graph = [[] for _ in vals]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    parent = list(range(size))
    weight = [1] * size

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def merge(first, second):
        first, second = find(first), find(second)
        if first == second:
            return
        if weight[first] < weight[second]:
            first, second = second, first
        parent[second] = first
        weight[first] += weight[second]

    order = sorted(range(size), key=vals.__getitem__)
    answer = 0
    begin = 0
    while begin < size:
        end = begin
        value = vals[order[begin]]
        while end < size and vals[order[end]] == value:
            for neighbor in graph[order[end]]:
                if vals[neighbor] <= value:
                    merge(order[end], neighbor)
            end += 1
        counts = {}
        for index in range(begin, end):
            root = find(order[index])
            counts[root] = counts.get(root, 0) + 1
        answer += sum(count * (count + 1) // 2 for count in counts.values())
        begin = end
    return answer


class Solution:
    def numberOfGoodPaths(self, vals: list[int], edges: list[list[int]]) -> int:
        return solve(vals, edges)
