"""Original frontend 3205 variant; qualification unknown."""


def solve(nums) -> int:
    ans = 0
    mx = 0
    for i in range(len(nums) - 1, 0, -1):
        if nums[i] > mx:
            mx = nums[i]
        ans += mx
    return ans


maxScore = solve


class Solution:
    def maxScore(self, nums) -> int:
        return solve(nums)
