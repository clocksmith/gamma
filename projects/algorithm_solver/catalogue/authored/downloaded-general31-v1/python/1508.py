"""1508. Range Sum of Sorted Subarray Sums (Medium).

Specification: https://leetcode.com/problems/range-sum-of-sorted-subarray-sums/description/
"""


def solve(nums: list[int], n: int, left: int, right: int) -> int:
    MOD = 1000000007
    sums = []
    for start in range(len(nums)):
        total = 0
        for end in range(start, len(nums)):
            total += nums[end]
            sums.append(total)
    sums.sort()
    answer = 0
    for i in range(left - 1, right):
        answer = (answer + sums[i]) % MOD
    return answer


class Solution:
    def rangeSum(self, nums: list[int], n: int, left: int, right: int) -> int:
        return solve(nums, n, left, right)
