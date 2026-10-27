"""3994. Minimum Adjacent Swaps to Partition Array.

Specification: https://leetcode.com/problems/minimum-adjacent-swaps-to-partition-array/description/
"""

from __future__ import annotations


def solve(nums: list[int], a: int, b: int) -> int:
    """O(n) time, O(1) auxiliary space. Inputs are preserved."""
    middle = high = answer = 0
    for value in nums:
        if value < a:
            answer = (answer + middle + high) % 1_000_000_007
        elif value <= b:
            answer = (answer + high) % 1_000_000_007
            middle += 1
        else:
            high += 1
    return answer

# Native judge method name is not established; canonical solve is the supported entry point.
