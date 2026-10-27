"""3982. Sum of Integers with Maximum Digit Range.

Specification: https://leetcode.com/problems/sum-of-integers-with-maximum-digit-range/description/
"""

from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n log M) time and O(1) auxiliary space. Inputs are preserved."""
    best_range = -1
    answer = 0
    for value in nums:
        remaining = value
        minimum, maximum = 9, 0
        while True:
            remaining, digit = divmod(remaining, 10)
            minimum = min(minimum, digit)
            maximum = max(maximum, digit)
            if remaining == 0:
                break
        digit_range = maximum - minimum
        if digit_range > best_range:
            best_range = digit_range
            answer = 0
        if digit_range == best_range:
            answer += value
    return answer

# Native judge method name is not established; canonical solve is the supported entry point.
