"""4007. Widest Possible Fence.

Specification: https://leetcode.com/problems/widest-possible-fence/description/
"""

from __future__ import annotations

from collections import Counter


def solve(planks: list[int]) -> int:
    """O(n+u^2) expected time and O(u^2) space; positive heights keep singles disjoint from complementary pairs. Inputs are preserved."""
    counts = Counter(planks)
    heights = list(counts)
    widths = dict(counts)
    answer = max(counts.values())
    for first, left in enumerate(heights):
        for second in range(first, len(heights)):
            right = heights[second]
            pairs = counts[left] // 2 if first == second else min(counts[left], counts[right])
            height = left + right
            widths[height] = widths.get(height, 0) + pairs
            answer = max(answer, widths[height])
    return answer
