"""4057. Number of Intersecting Interval Pairs II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/number-of-intersecting-interval-pairs-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4057.Number%20of%20Intersecting%20Interval%20Pairs%20II/README_EN.md
Complexity: O(n log n) time, O(n) space.
Closed endpoints intersect. Each strictly disjoint pair is subtracted once. Inputs preserved.
"""

from __future__ import annotations

def solve(intervals):
    starts = sorted(a for a, _ in intervals)
    ends = sorted(b for _, b in intervals)
    n = len(intervals)
    answer, finished = n*(n-1)//2, 0
    for start in starts:
        while finished < n and ends[finished] < start:
            finished += 1
        answer -= finished
    return answer


class Solution:
    def countIntersectingIntervals(self, intervals):
        return solve(intervals)
