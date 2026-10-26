"""2374. Node With Highest Edge Score: sum incoming source indices and preserve the smallest identifier on ties."""


def solve(edges: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    scores = [0] * len(edges)
    for source, target in enumerate(edges):
        scores[target] += source
    answer = 0
    for node in range(1, len(edges)):
        if scores[node] > scores[answer]:
            answer = node
    return answer


class Solution:
    def edgeScore(self, edges: list[int]) -> int:
        return solve(edges)
