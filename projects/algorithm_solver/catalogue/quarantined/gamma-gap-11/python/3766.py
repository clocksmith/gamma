"""3766. Minimum Operations to Make Binary Palindrome."""
from __future__ import annotations
from bisect import bisect_left


def solve(nums: list[int]) -> list[int]:
    """O(M log M + n log M) time and O(M) space, M the next power of two above max(nums) <= 5000."""
    limit = 1 << max(nums).bit_length()
    palindromes = [0]
    for value in range(1, limit):
        digits = format(value, 'b')
        if digits == digits[::-1]:
            palindromes.append(value)
    answer = []
    for value in nums:
        index = bisect_left(palindromes, value)
        distance = abs(value - palindromes[index - 1])
        if index < len(palindromes):
            distance = min(distance, palindromes[index] - value)
        answer.append(distance)
    return answer


class Solution:
    def minOperations(self, nums: list[int]) -> list[int]:
        return solve(nums)
