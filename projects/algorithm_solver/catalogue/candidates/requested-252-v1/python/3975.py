"""3975. Filter Occupied Intervals
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/filter-occupied-intervals/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3975.Filter%20Occupied%20Intervals/README_EN.md
Complexity: O(n log n) time, O(n) space.
Inclusive integer intervals; touching intervals merge. Remove free points rather than retaining the intersection. Inputs and row objects preserved.
"""

from __future__ import annotations

def solve(occupiedIntervals, freeStart, freeEnd):
    merged = []
    for start, end in sorted(occupiedIntervals):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    answer = []
    for start, end in merged:
        if end < freeStart or start > freeEnd:
            answer.append([start, end])
        else:
            if start < freeStart:
                answer.append([start, freeStart - 1])
            if end > freeEnd:
                answer.append([freeEnd + 1, end])
    return answer


class Solution:
    def filterOccupiedIntervals(self, occupiedIntervals, freeStart, freeEnd):
        return solve(occupiedIntervals, freeStart, freeEnd)
