"""3960. Frequency Balance Subarray.

Specification: https://leetcode.com/problems/frequency-balance-subarray/description/
"""

from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n^2) expected time and O(n) space; two different frequencies must both occur unless there is one distinct value. Inputs are preserved."""
    answer = 1
    for left in range(len(nums)):
        counts, frequencies = {}, {}
        for right in range(left, len(nums)):
            value = nums[right]
            old = counts.get(value, 0)
            if old:
                frequencies[old] -= 1
                if frequencies[old] == 0:
                    del frequencies[old]
            counts[value] = old + 1
            frequencies[old + 1] = frequencies.get(old + 1, 0) + 1
            valid = len(counts) == 1
            if len(frequencies) == 2:
                first, second = frequencies
                valid = max(first, second) == 2 * min(first, second)
            if valid:
                answer = max(answer, right - left + 1)
    return answer
