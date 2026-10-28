"""3296. Minimum Number of Seconds to Make Mountain Height Zero (Medium).

Specification: https://leetcode.com/problems/minimum-number-of-seconds-to-make-mountain-height-zero/description/
"""


def solve(mountainHeight: int, workerTimes: list[int]) -> int:
    import math

    def enough(mid: int) -> bool:
        total = 0
        for w in workerTimes:
            total += int((math.sqrt(1 + 8 * mid / w) - 1) // 2)
            if total >= mountainHeight:
                return True
        return total >= mountainHeight

    wmax = max(workerTimes)
    lo, hi = 0, wmax * mountainHeight * (mountainHeight + 1) // 2
    while lo < hi:
        mid = (lo + hi) // 2
        if enough(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


class Solution:
    def minNumberOfSeconds(self, mountainHeight: int, workerTimes: list[int]) -> int:
        return solve(mountainHeight, workerTimes)
