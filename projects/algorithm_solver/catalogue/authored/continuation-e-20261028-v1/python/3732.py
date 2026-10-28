def solve(nums):
    first = second = 0
    for x in nums:
        x = abs(x)
        if x >= first:
            first, second = x, first
        elif x > second:
            second = x
    return 100000 * first * second


class Solution:
    def maxProduct(self, nums):
        return solve(nums)
