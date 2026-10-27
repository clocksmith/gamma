"""312. Burst Balloons."""
def solve(nums: list[int]) -> int:
    values = [1] + [value for value in nums if value] + [1]
    size = len(values)
    dp = [[0] * size for _ in range(size)]
    for length in range(2, size):
        for left in range(size - length):
            right = left + length
            dp[left][right] = max((dp[left][middle] + values[left] * values[middle] * values[right] + dp[middle][right]
                                   for middle in range(left + 1, right)), default=0)
    return dp[0][-1]

class Solution:
    def maxCoins(self, nums: list[int]) -> int:
        return solve(nums)
