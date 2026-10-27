"""4026. Maximum Gap Between Stations
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-gap-between-stations/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4026.Maximum%20Gap%20Between%20Stations/README_EN.md
Complexity: O(|skill|+|station|) time, O(|skill|) space.
Earliest prefix and latest suffix maximize each consecutive-worker gap. A valid complete assignment is guaranteed; one worker returns zero.
"""

from __future__ import annotations

def solve(skill, station):
    count = len(skill)
    latest = [0] * count
    j = len(station) - 1
    for i in range(count - 1, -1, -1):
        while station[j] != skill[i]:
            j -= 1
        latest[i] = j
        j -= 1
    answer = j = 0
    for i in range(count - 1):
        while station[j] != skill[i]:
            j += 1
        answer = max(answer, latest[i + 1] - j)
        j += 1
    return answer


class Solution:
    def maximumGap(self, skill, station):
        return solve(skill, station)
