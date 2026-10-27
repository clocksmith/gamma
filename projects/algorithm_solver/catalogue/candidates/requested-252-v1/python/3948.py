"""3948. Lexicographically Maximum MEX Array.

Specification: https://leetcode.com/problems/lexicographically-maximum-mex-array/description/
"""

from __future__ import annotations


def solve(nums: list[int]) -> list[int]:
    """O(n) time and O(n) space; take the shortest prefix realizing each suffix MEX. Inputs are preserved."""
    size = len(nums)
    suffix_mex = [0] * size
    present = bytearray(size + 1)
    mex = 0
    for index in range(size - 1, -1, -1):
        if nums[index] <= size:
            present[nums[index]] = 1
        while mex <= size and present[mex]:
            mex += 1
        suffix_mex[index] = mex
    answer = []
    seen = [0] * (size + 1)
    generation = start = 0
    while start < size:
        wanted = suffix_mex[start]
        answer.append(wanted)
        if wanted == 0:
            start += 1
            continue
        generation += 1
        needed = wanted
        while needed:
            value = nums[start]
            start += 1
            if value < wanted and seen[value] != generation:
                seen[value] = generation
                needed -= 1
    return answer
