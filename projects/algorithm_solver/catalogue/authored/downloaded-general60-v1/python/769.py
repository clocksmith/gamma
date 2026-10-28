"""769. Max Chunks To Make Sorted (Medium).

Specification: https://leetcode.com/problems/max-chunks-to-make-sorted/description/
"""


def solve(arr: list[int]) -> int:
    chunks = 0
    max_value = 0
    for i, value in enumerate(arr):
        max_value = max(max_value, value)
        if max_value == i:
            chunks += 1
    return chunks


class Solution:
    def maxChunksToSorted(self, arr: list[int]) -> int:
        return solve(arr)
