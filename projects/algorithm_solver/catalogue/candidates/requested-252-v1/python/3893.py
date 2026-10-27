"""3893. Maximum Team Size with Overlapping Intervals
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-team-size-with-overlapping-intervals/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3893.Maximum%20Team%20Size%20with%20Overlapping%20Intervals/README_EN.md
Complexity: O(n log n) time, O(n) space.
Closed intervals. One central interval must meet all members; pairwise common intersection is not required. Inputs preserved.
"""

from __future__ import annotations
from bisect import bisect_left, bisect_right

def solve(startTime, endTime):
    starts = sorted(startTime)
    ends = sorted(endTime)
    return max(bisect_right(starts, right) - bisect_left(ends, left) for left, right in zip(startTime, endTime))


class Solution:
    def maximumTeamSize(self, startTime, endTime):
        return solve(startTime, endTime)
