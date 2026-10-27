"""376. Wiggle Subsequence."""
def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    up = down = 1
    for left, right in zip(nums, nums[1:]):
        if right > left:
            up = down + 1
        elif right < left:
            down = up + 1
    return max(up, down)

class Solution:
    def wiggleMaxLength(self, nums: list[int]) -> int:
        return solve(nums)
