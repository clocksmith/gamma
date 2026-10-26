"""3728. Stable Subarrays With Equal Boundary and Interior Sum."""
from __future__ import annotations


def solve(capacity: list[int]) -> int:
    """O(n) expected time and O(n) space; prefix sums handle negative values and enforce length >= 3."""
    prefix = [0]
    for value in capacity:
        prefix.append(prefix[-1] + value)
    counts = {}
    answer = 0
    for right in range(2, len(capacity)):
        left = right - 2
        key = (capacity[left], prefix[left + 1] + capacity[left])
        counts[key] = counts.get(key, 0) + 1
        answer += counts.get((capacity[right], prefix[right]), 0)
    return answer


class Solution:
    def countStableSubarrays(self, capacity: list[int]) -> int:
        return solve(capacity)
