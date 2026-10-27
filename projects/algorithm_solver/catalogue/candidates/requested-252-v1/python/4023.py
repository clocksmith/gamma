"""4023. Elevator Requests II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/elevator-requests-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4023.Elevator%20Requests%20II/README_EN.md
Complexity: O(q^2) time, O(q) space.
Served floors form an interval containing start. Each expansion charges distance times outstanding requests. Start is a zero-penalty dummy if not requested; distinct requested floors only. Inputs preserved; native method unconfirmed.
"""

from __future__ import annotations

def solve(n, start, requests):
    points = sorted(set(requests) | {start})
    size = len(points)
    origin = points.index(start)
    left = [float('inf')] * size
    right = [float('inf')] * size
    left[origin] = right[origin] = 0
    for length in range(1, size):
        next_left = [float('inf')] * size
        next_right = [float('inf')] * size
        waiting = size - length
        for lo in range(max(0, origin - length + 1), min(origin, size - length) + 1):
            hi = lo + length - 1
            if lo:
                next_left[lo - 1] = min(next_left[lo - 1], left[lo] + (points[lo] - points[lo - 1]) * waiting, right[lo] + (points[hi] - points[lo - 1]) * waiting)
            if hi + 1 < size:
                next_right[lo] = min(next_right[lo], left[lo] + (points[hi + 1] - points[lo]) * waiting, right[lo] + (points[hi + 1] - points[hi]) * waiting)
        left, right = next_left, next_right
    return min(left[0], right[0])
