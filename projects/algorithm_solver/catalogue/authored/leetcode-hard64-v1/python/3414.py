"""3414. Maximum Score of Non-overlapping Intervals: weighted interval scheduling with bounded cardinality and explicit tie-breaking."""

from bisect import bisect_left


def solve(intervals: list[list[int]]) -> list[int]:
    """O(n log n) time and O(n) auxiliary space; at most four indices per state. Inputs are preserved."""
    ordered = sorted((end, start, weight, index) for index, (start, end, weight) in enumerate(intervals))
    ends = [entry[0] for entry in ordered]
    predecessors = [bisect_left(ends, start) for _, start, _, _ in ordered]
    n = len(ordered)
    previous = [(0, ()) for _ in range(n + 1)]
    for _ in range(4):
        current = [(0, ()) for _ in range(n + 1)]
        for position, (_, _, weight, index) in enumerate(ordered, 1):
            score, indices = previous[predecessors[position - 1]]
            candidate = (score + weight, tuple(sorted((*indices, index))))
            incumbent = current[position - 1]
            if candidate[0] > incumbent[0] or (candidate[0] == incumbent[0] and candidate[1] < incumbent[1]):
                current[position] = candidate
            else:
                current[position] = incumbent
        previous = current
    return list(previous[n][1])


class Solution:
    def maximumWeight(self, intervals: list[list[int]]) -> list[int]:
        return solve(intervals)
