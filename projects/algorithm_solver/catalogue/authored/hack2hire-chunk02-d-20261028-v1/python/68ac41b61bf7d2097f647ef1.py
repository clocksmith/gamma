"""Hack2Hire 68ac41b61bf7d2097f647ef1 (Design Request Rate limiter) over an INFERRED spec; qualification unknown."""
from collections import deque


def solve(timestamps, windowSize, maxRequests):
    window = deque()
    result = []
    for t in timestamps:
        low = t - windowSize + 1
        while window and window[0] < low:
            window.popleft()
        allowed = len(window) < maxRequests
        if allowed:
            window.append(t)
        result.append(allowed)
    return result


class Solution:
    def rateLimit(self, timestamps, windowSize, maxRequests):
        return solve(timestamps, windowSize, maxRequests)
