"""2359. Find Closest Node to Given Two Nodes: record both functional-graph distances and minimize the larger one."""


def solve(edges: list[int], node1: int, node2: int) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    def distances(start: int) -> list[int]:
        result = [-1] * len(edges)
        node = start
        distance = 0
        while node != -1 and result[node] == -1:
            result[node] = distance
            distance += 1
            node = edges[node]
        return result

    first, second = distances(node1), distances(node2)
    answer = -1
    best = len(edges) + 1
    for node in range(len(edges)):
        if first[node] >= 0 and second[node] >= 0:
            cost = max(first[node], second[node])
            if cost < best:
                answer, best = node, cost
    return answer


class Solution:
    def closestMeetingNode(self, edges: list[int], node1: int, node2: int) -> int:
        return solve(edges, node1, node2)
