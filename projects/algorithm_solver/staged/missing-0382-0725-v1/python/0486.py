"""486. Predict the Winner. Interval minimax expressed as the current player's score advantage."""

def solve(nums: list[int]) -> bool:
    dp = nums[:]
    for left in range(len(nums) - 2, -1, -1):
        for right in range(left + 1, len(nums)):
            dp[right] = max(nums[left] - dp[right], nums[right] - dp[right - 1])
    return not nums or dp[-1] >= 0


class Solution:
    def predictTheWinner(self, nums: list[int]) -> bool:
        return solve(nums)
