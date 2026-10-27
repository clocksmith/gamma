"""4029. Elevator Requests IV
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/elevator-requests-iv/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4029.Elevator%20Requests%20IV/README_EN.md
Complexity: O(q^2 log U) time, O(q) space; U bounds finishing time.
Binary search finish time T. Reverse time: releases become deadlines T-arrival, final floor is free, and the route ends at start by time T. Earliest reversed arrival dominates later arrivals. Visited request floors form an interval, yielding exact interval DP. Repeated floors retain only latest release. Inputs preserved; new derivation is unexecuted.
"""

from __future__ import annotations

def solve(n, start, requests):
    arrivals = {}
    for time, floor in requests:
        arrivals[floor] = max(arrivals.get(floor, 0), time)
    points = sorted(arrivals)
    releases = [arrivals[x] for x in points]
    count = len(points)
    low = max(releases)
    high = low + points[-1] - points[0] + min(abs(start - points[0]), abs(start - points[-1]))
    def feasible(finish):
        left = right = [0] * count
        for length in range(2, count + 1):
            next_left = [float('inf')] * (count - length + 1)
            next_right = [float('inf')] * (count - length + 1)
            for lo in range(count - length + 1):
                hi = lo + length - 1
                a = min(left[lo + 1] + points[lo + 1] - points[lo], right[lo + 1] + points[hi] - points[lo])
                if a <= finish - releases[lo]:
                    next_left[lo] = a
                b = min(left[lo] + points[hi] - points[lo], right[lo] + points[hi] - points[hi - 1])
                if b <= finish - releases[hi]:
                    next_right[lo] = b
            left, right = next_left, next_right
        return min(left[0] + abs(points[0] - start), right[0] + abs(points[-1] - start)) <= finish
    while low < high:
        middle = (low + high) // 2
        if feasible(middle):
            high = middle
        else:
            low = middle + 1
    return low
