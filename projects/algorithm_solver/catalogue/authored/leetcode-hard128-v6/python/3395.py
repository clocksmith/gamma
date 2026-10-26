"""3395. Subsequences with a Unique Middle Mode I.

Separate middle frequencies at least three from frequency two with three distinct other values; O(n*U) time and O(U) space. Inputs are preserved.
"""

from collections import Counter


def solve(nums: list[int]) -> int:
    modulus = 1_000_000_007
    left, right = Counter(), Counter(nums)
    values = list(right)

    def choose(count, amount):
        if amount == 0:
            return 1
        if amount == 1:
            return count
        return count * (count - 1) // 2

    left_pairs = 0
    right_pairs = sum(choose(count, 2) for count in right.values())
    answer = 0
    for index, middle in enumerate(nums):
        right_pairs -= right[middle] - 1
        right[middle] -= 1
        a, b = left[middle], right[middle]
        other_left, other_right = index - a, len(nums) - index - 1 - b
        ways = 0
        for first in range(3):
            for second in range(3):
                if first + second >= 2:
                    ways += (choose(a, first) * choose(other_left, 2 - first)
                             * choose(b, second) * choose(other_right, 2 - second))
        duplicate_left = left_pairs - choose(a, 2)
        duplicate_right = right_pairs - choose(b, 2)
        for value in values:
            if value == middle:
                continue
            l_count, r_count = left[value], right[value]
            ways += a * l_count * (choose(other_right - r_count, 2) - duplicate_right + choose(r_count, 2))
            ways += b * r_count * (choose(other_left - l_count, 2) - duplicate_left + choose(l_count, 2))
        answer = (answer + ways) % modulus
        left_pairs += a
        left[middle] += 1
    return answer


class Solution:
    def subsequencesWithMiddleMode(self, nums: list[int]) -> int:
        return solve(nums)
