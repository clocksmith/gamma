"""4025. Minimize the Maximum Waiting Time at Synchronized Traffic Lights
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimize-the-maximum-waiting-time-at-synchronized-traffic-lights/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4025.Minimize%20the%20Maximum%20Waiting%20Time%20at%20Synchronized%20Traffic%20Lights/README_EN.md
Complexity: O(|lights|+|arrivalTime|) time, O(1) space.
Unlimited simultaneous cars make the longest green phase weakly optimal for every car. Equality with green duration is red.
"""

from __future__ import annotations

def solve(period, lights, arrivalTime):
    green = max(lights)
    return max((period - time % period if time % period >= green else 0 for time in arrivalTime), default=0)


class Solution:
    def minPenalty(self, period, lights, arrivalTime):
        return solve(period, lights, arrivalTime)
