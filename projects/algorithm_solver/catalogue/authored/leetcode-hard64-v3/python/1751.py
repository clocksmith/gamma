"""1751. Maximum Number of Events That Can Be Attended II: event-count DP with binary-searched successors; O(n log n+n*k) time and O(n) space."""

from bisect import bisect_right


def solve(events: list[list[int]], k: int) -> int:
    ordered = sorted(events)
    size = len(ordered)
    starts = [event[0] for event in ordered]
    following = [bisect_right(starts, event[1], index + 1) for index, event in enumerate(ordered)]
    previous = [0] * (size + 1)
    for _ in range(min(k, size)):
        current = [0] * (size + 1)
        for index in range(size - 1, -1, -1):
            current[index] = max(current[index + 1], ordered[index][2] + previous[following[index]])
        previous = current
    return previous[0]


class Solution:
    def maxValue(self, events: list[list[int]], k: int) -> int:
        return solve(events, k)
