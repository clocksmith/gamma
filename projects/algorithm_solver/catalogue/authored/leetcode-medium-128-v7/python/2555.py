"""2555. Maximize Win From Two Segments: combine each sliding segment with the best earlier disjoint segment."""


def solve(prizePositions: list[int], k: int) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    best_prefix = [0] * (len(prizePositions) + 1)
    left = best = 0
    for right, position in enumerate(prizePositions):
        while position - prizePositions[left] > k:
            left += 1
        width = right - left + 1
        best = max(best, width + best_prefix[left])
        best_prefix[right + 1] = max(best_prefix[right], width)
    return best


class Solution:
    def maximizeWin(self, prizePositions: list[int], k: int) -> int:
        return solve(prizePositions, k)
