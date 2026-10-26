"""2141. Maximum Running Time of N Computers."""


def solve(n: int, batteries: list[int]) -> int:
    """Binary search using clipped total energy; O(m log(sum(batteries))) time, O(1) auxiliary space. Inputs are preserved."""
    left, right = 0, sum(batteries) // n
    while left < right:
        duration = (left + right + 1) // 2
        available = sum(min(capacity, duration) for capacity in batteries)
        if available >= n * duration:
            left = duration
        else:
            right = duration - 1
    return left


class Solution:
    def maxRunTime(self, n: int, batteries: list[int]) -> int:
        return solve(n, batteries)
