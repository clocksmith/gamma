"""2035. Partition Array Into Two Arrays to Minimize Sum Difference."""

from bisect import bisect_left


def solve(nums: list[int]) -> int:
    """Meet-in-the-middle sums grouped by cardinality; O(n*2^n) time and O(2^n) space for 2n values. Inputs are preserved."""
    half = len(nums) // 2

    def grouped(values):
        groups = [[] for _ in range(half + 1)]
        groups[0] = [0]
        for index, value in enumerate(values):
            for count in range(index + 1, 0, -1):
                groups[count].extend(total + value for total in groups[count - 1])
        return groups

    left = grouped(nums[:half])
    right = grouped(nums[half:])
    total = sum(nums)
    answer = abs(total - 2 * sum(nums[:half]))
    for count, sums in enumerate(left):
        choices = sorted(right[half - count])
        for subtotal in sums:
            position = bisect_left(choices, total / 2 - subtotal)
            for index in (position - 1, position):
                if 0 <= index < len(choices):
                    answer = min(answer, abs(total - 2 * (subtotal + choices[index])))
    return answer


class Solution:
    def minimumDifference(self, nums: list[int]) -> int:
        return solve(nums)
