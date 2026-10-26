"""2242. Maximum Score of a Node Sequence."""


def solve(scores: list[int], edges: list[list[int]]) -> int:
    """Three best neighbors at each end of the middle edge; O(V+E) time and O(V) auxiliary space. Inputs are preserved."""
    neighbors = [[] for _ in scores]

    def add_neighbor(source, target):
        neighbors[source].append(target)
        neighbors[source].sort(key=lambda node: scores[node], reverse=True)
        if len(neighbors[source]) > 3:
            neighbors[source].pop()

    for first, second in edges:
        add_neighbor(first, second)
        add_neighbor(second, first)
    answer = -1
    for first, second in edges:
        for left in neighbors[first]:
            if left == second:
                continue
            for right in neighbors[second]:
                if right != first and right != left:
                    answer = max(answer, scores[left] + scores[first] + scores[second] + scores[right])
    return answer


class Solution:
    def maximumScore(self, scores: list[int], edges: list[list[int]]) -> int:
        return solve(scores, edges)
