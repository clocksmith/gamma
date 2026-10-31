"""Original frontend 2936 variant; qualification unknown."""


def solve(nums) -> int:
    if isinstance(nums, list):
        n = len(nums)
        get_at = lambda idx: nums[idx]
    else:
        n = nums.size()
        get_at = nums.at
    blocks = 0
    i = 0
    while i < n:
        val = get_at(i)
        lo, hi = i, n - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if get_at(mid) == val:
                lo = mid
            else:
                hi = mid - 1
        blocks += 1
        i = lo + 1
    return blocks


countBlocks = solve


class Solution:
    def countBlocks(self, nums) -> int:
        return solve(nums)
