"""2054. Two Best Non-Overlapping Events (Medium).

Specification: https://leetcode.com/problems/two-best-non-overlapping-events/description/
"""


def solve(events: list[list[int]]) -> int:
    sorted_events = sorted([list(e) for e in events])
    n = len(sorted_events)
    suffix = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix[i] = max(suffix[i + 1], sorted_events[i][2])
    best = 0
    for event in sorted_events:
        left, right = 0, n
        while left < right:
            mid = (left + right) // 2
            if sorted_events[mid][0] > event[1]:
                right = mid
            else:
                left = mid + 1
        value = event[2] + (suffix[left] if left < n else 0)
        best = max(best, value)
    return best


class Solution:
    def maxTwoEvents(self, events: list[list[int]]) -> int:
        return solve(events)
