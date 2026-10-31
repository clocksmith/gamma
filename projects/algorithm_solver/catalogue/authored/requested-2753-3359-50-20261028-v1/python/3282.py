"""Original frontend 3282 variant; qualification unknown."""


def solve(nums) -> int:
    ans = 0
    mx = 0
    for i in range(len(nums) - 1):
        if nums[i] > mx:
            mx = nums[i]
        ans += mx
    return ans


findMaximumScore = solve


class Solution:
    def findMaximumScore(self, nums) -> int:
        return solve(nums)
