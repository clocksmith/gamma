"""1743. Restore the Array From Adjacent Pairs: walk the path from its smaller endpoint."""


def solve(adjacentPairs: list[list[int]]) -> list[int]:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    graph = {}
    for left, right in adjacentPairs:
        graph.setdefault(left, []).append(right)
        graph.setdefault(right, []).append(left)
    start = min(value for value, neighbors in graph.items() if len(neighbors) == 1)
    answer = [start]
    previous = None
    current = start
    while len(answer) < len(graph):
        for neighbor in graph[current]:
            if neighbor != previous:
                answer.append(neighbor)
                previous, current = current, neighbor
                break
    return answer


class Solution:
    def restoreArray(self, adjacentPairs: list[list[int]]) -> list[int]:
        return solve(adjacentPairs)
