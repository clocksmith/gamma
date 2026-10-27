"""3661. Maximum Walls Destroyed by Robots
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-walls-destroyed-by-robots/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3661.Maximum%20Walls%20Destroyed%20by%20Robots/README_EN.md
Complexity: O(n log n + m log m + n log m) time; O(n+m) space.
Inputs preserved. Robot-position walls counted once independently; gap DP counts unions without double counting.
"""

from __future__ import annotations
from bisect import bisect_left, bisect_right

def solve(robots, distance, walls):
    machines = sorted(zip(robots, distance))
    positions = {position for position, _ in machines}
    fixed = sum(wall in positions for wall in walls)
    remaining = sorted(wall for wall in walls if wall not in positions)
    def count(left, right):
        if left > right:
            return 0
        return bisect_right(remaining, right) - bisect_left(remaining, left)
    first, reach = machines[0]
    left_score, right_score = count(first - reach, first - 1), 0
    for i in range(len(machines) - 1):
        left, left_reach = machines[i]
        right, right_reach = machines[i + 1]
        right_end = min(right - 1, left + left_reach)
        left_start = max(left + 1, right - right_reach)
        from_left = count(left + 1, right_end)
        from_right = count(left_start, right - 1)
        overlap = count(left_start, right_end)
        next_left = max(left_score + from_right, right_score + from_left + from_right - overlap)
        next_right = max(left_score, right_score + from_left)
        left_score, right_score = next_left, next_right
    last, reach = machines[-1]
    return fixed + max(left_score, right_score + count(last + 1, last + reach))


class Solution:
    def maxWalls(self, robots, distance, walls):
        return solve(robots, distance, walls)
