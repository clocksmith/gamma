"""546. Remove Boxes (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/remove-boxes/description/
Canonical API: solve(boxes); also exposes Solution.removeBoxes.
Inputs are preserved. Gamma independent qualification is pending.
"""

from functools import lru_cache


def solve(boxes: list[int]) -> int:
    colors = []
    counts = []
    for color in boxes:
        if colors and colors[-1] == color:
            counts[-1] += 1
        else:
            colors.append(color)
            counts.append(1)

    @lru_cache(maxsize=None)
    def best_score(left: int, right: int, carried: int) -> int:
        if left > right:
            return 0
        merged_count = counts[right] + carried
        best = best_score(left, right - 1, 0) + merged_count * merged_count
        for middle in range(left, right):
            if colors[middle] == colors[right]:
                best = max(
                    best,
                    best_score(left, middle, merged_count)
                    + best_score(middle + 1, right - 1, 0),
                )
        return best

    answer = best_score(0, len(colors) - 1, 0)
    best_score.cache_clear()
    return answer

class Solution:
    def removeBoxes(self, boxes: list[int]) -> int:
        return solve(boxes)
