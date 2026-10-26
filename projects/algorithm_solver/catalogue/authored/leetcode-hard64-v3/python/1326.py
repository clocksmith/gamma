"""1326. Minimum Number of Taps to Open to Water a Garden: greedy interval coverage; O(n) time and O(n) space. Inputs are preserved."""


def solve(n: int, ranges: list[int]) -> int:
    reach = [0] * (n + 1)
    for position, radius in enumerate(ranges):
        left = max(0, position - radius)
        reach[left] = max(reach[left], min(n, position + radius))
    taps = boundary = farthest = 0
    for position in range(n):
        farthest = max(farthest, reach[position])
        if position == boundary:
            if farthest <= position:
                return -1
            taps += 1
            boundary = farthest
    return taps


class Solution:
    def minTaps(self, n: int, ranges: list[int]) -> int:
        return solve(n, ranges)
