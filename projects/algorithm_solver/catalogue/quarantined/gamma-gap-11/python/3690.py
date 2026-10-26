"""3690. Split and Merge Array Transformation."""
from __future__ import annotations
from collections import deque


def solve(nums1: list[int], nums2: list[int]) -> int:
    """O(n! * n^4) time and O(n! * n) space, with n <= 6; inputs are preserved."""
    start = tuple(nums1)
    target = tuple(nums2)
    if start == target:
        return 0
    queue = deque([(start, 0)])
    seen = {start}
    n = len(start)
    while queue:
        state, distance = queue.popleft()
        for left in range(n):
            for right in range(left + 1, n + 1):
                block = state[left:right]
                rest = state[:left] + state[right:]
                for position in range(len(rest) + 1):
                    following = rest[:position] + block + rest[position:]
                    if following == target:
                        return distance + 1
                    if following not in seen:
                        seen.add(following)
                        queue.append((following, distance + 1))
    return -1


class Solution:
    def minSplitMerge(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
