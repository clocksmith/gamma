"""3986. Number of Elapsed Seconds Between Two Times
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/number-of-elapsed-seconds-between-two-times/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3986.Number%20of%20Elapsed%20Seconds%20Between%20Two%20Times/README_EN.md
Complexity: O(1) time and space.
Valid same-day times with endTime >= startTime; no invented midnight rollover.
"""

from __future__ import annotations

def solve(startTime, endTime):
    def seconds(value):
        h, m, s = map(int, value.split(':'))
        return h * 3600 + m * 60 + s
    return seconds(endTime) - seconds(startTime)


class Solution:
    def secondsBetweenTimes(self, startTime, endTime):
        return solve(startTime, endTime)
