"""2497. Maximum Star Sum of a Graph: add at most k positive neighbor values to each possible center."""


def solve(vals: list[int], edges: list[list[int]], k: int) -> int:
    """O(n + e * log(e + 1)) time and O(n + e) auxiliary space; inputs are read-only."""
    answer = max(vals)
    if k == 0:
        return answer
    neighbors = [[] for _ in vals]
    seen_edges = set()
    for left, right in edges:
        edge = (min(left, right), max(left, right))
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        if vals[right] > 0:
            neighbors[left].append(vals[right])
        if vals[left] > 0:
            neighbors[right].append(vals[left])
    for node, values in enumerate(neighbors):
        values.sort(reverse=True)
        total = vals[node]
        for index in range(min(k, len(values))):
            total += values[index]
        answer = max(answer, total)
    return answer


class Solution:
    def maxStarSum(self, vals: list[int], edges: list[list[int]], k: int) -> int:
        return solve(vals, edges, k)
