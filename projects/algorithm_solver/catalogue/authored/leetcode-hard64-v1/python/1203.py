"""1203. Sort Items by Groups Respecting Dependencies: separate group and item topological orders."""


def solve(n: int, m: int, group: list[int], beforeItems: list[list[int]]) -> list[int]:
    """O(n + m + E) time and space, E = prerequisite count. Inputs are preserved."""
    groups = group[:]
    group_count = m
    for item in range(n):
        if groups[item] == -1:
            groups[item] = group_count
            group_count += 1
    item_edges = [[] for _ in range(n)]
    item_degree = [0] * n
    group_edges = [[] for _ in range(group_count)]
    group_seen = [set() for _ in range(group_count)]
    group_degree = [0] * group_count
    for item, prerequisites in enumerate(beforeItems):
        for previous in prerequisites:
            item_edges[previous].append(item)
            item_degree[item] += 1
            source, destination = groups[previous], groups[item]
            if source != destination and destination not in group_seen[source]:
                group_seen[source].add(destination)
                group_edges[source].append(destination)
                group_degree[destination] += 1

    def topological(edges, degree):
        order = [node for node, count in enumerate(degree) if count == 0]
        head = 0
        while head < len(order):
            node = order[head]
            head += 1
            for following in edges[node]:
                degree[following] -= 1
                if degree[following] == 0:
                    order.append(following)
        return order if len(order) == len(edges) else []

    item_order = topological(item_edges, item_degree)
    group_order = topological(group_edges, group_degree)
    if len(item_order) != n or len(group_order) != group_count:
        return []
    buckets = [[] for _ in range(group_count)]
    for item in item_order:
        buckets[groups[item]].append(item)
    return [item for identifier in group_order for item in buckets[identifier]]


class Solution:
    def sortItems(self, n: int, m: int, group: list[int], beforeItems: list[list[int]]) -> list[int]:
        return solve(n, m, group, beforeItems)
