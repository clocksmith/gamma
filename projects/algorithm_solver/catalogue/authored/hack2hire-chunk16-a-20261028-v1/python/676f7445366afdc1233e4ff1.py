"""Hack2Hire 676f7445366afdc1233e4ff1 (Maximum Sprint Points Sum) over an INFERRED spec; qualification unknown."""


def solve(days, k):
    doubled = days + days
    m = len(doubled)
    day_prefix = [0] * (m + 1)
    point_prefix = [0] * (m + 1)
    for i in range(m):
        d = doubled[i]
        day_prefix[i + 1] = day_prefix[i] + d
        point_prefix[i + 1] = point_prefix[i] + d * (d + 1) // 2
    best = 0
    left = 0
    for right in range(len(days), m):
        while day_prefix[right + 1] - day_prefix[left + 1] >= k:
            left += 1
        full_days = day_prefix[right + 1] - day_prefix[left + 1]
        value = point_prefix[right + 1] - point_prefix[left + 1]
        rest = k - full_days
        d = doubled[left]
        value += (d * (d + 1) - (d - rest) * (d - rest + 1)) // 2
        if value > best:
            best = value
    return best


class Solution:
    def maxSprintPoints(self, days, k):
        return solve(days, k)
