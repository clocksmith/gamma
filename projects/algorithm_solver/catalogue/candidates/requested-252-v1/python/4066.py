"""4066. Maximum Equal Adjacent Pairs After at Most One Replacement.

Specification: https://leetcode.com/problems/maximum-equal-adjacent-pairs-after-at-most-one-replacement/description/
"""

from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) space; count adjacent unordered unequal-value pairs. Inputs are preserved."""
    counts = {}
    equal = gain = 0
    for index in range(1, len(nums)):
        left, right = nums[index - 1], nums[index]
        if left == right:
            equal += 1
            continue
        key = (min(left, right), max(left, right))
        counts[key] = counts.get(key, 0) + 1
        gain = max(gain, counts[key])
    return equal + gain

# Native judge method name is not established; canonical solve is the supported entry point.
