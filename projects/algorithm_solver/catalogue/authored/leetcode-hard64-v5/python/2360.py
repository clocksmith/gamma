"""2360. Longest Cycle in a Graph. Timestamp each walk and recognize cycles within its own visit interval."""


def solve(edges: list[int]) -> int:
    """O(n) time and O(n) space. Inputs are preserved."""
    visited = [0] * len(edges)
    clock = 1
    answer = -1
    for start in range(len(edges)):
        if visited[start]:
            continue
        beginning = clock
        node = start
        while node != -1 and visited[node] == 0:
            visited[node] = clock
            clock += 1
            node = edges[node]
        if node != -1 and visited[node] >= beginning:
            answer = max(answer, clock - visited[node])
    return answer


class Solution:
    def longestCycle(self, edges: list[int]) -> int:
        return solve(edges)
