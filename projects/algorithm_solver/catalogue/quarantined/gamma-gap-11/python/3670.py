"""3670. Maximum Product of Two Integers With No Common Bits."""
from __future__ import annotations


def solve(nums: list[int]) -> int:
    """O(n + B * 2^B) time and O(2^B) auxiliary space; B <= 20. Inputs are preserved."""
    width = max(nums).bit_length()
    size = 1 << width
    best = [0] * size
    for value in nums:
        best[value] = value
    bit = 1
    while bit < size:
        for start in range(0, size, 2 * bit):
            for offset in range(bit):
                index = start + bit + offset
                best[index] = max(best[index], best[index - bit])
        bit <<= 1
    mask = size - 1
    answer = 0
    for value in nums:
        answer = max(answer, value * best[mask ^ value])
    return answer


class Solution:
    def maxProduct(self, nums: list[int]) -> int:
        return solve(nums)
