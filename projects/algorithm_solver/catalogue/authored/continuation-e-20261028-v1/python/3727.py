def solve(nums):
    squares = sorted(x * x for x in nums)
    return sum(squares) - 2 * sum(squares[:len(nums) // 2])


class Solution:
    def maxAlternatingSum(self, nums):
        return solve(nums)
