def solve(nums1):
    return min(nums1) % 2 == 1 or all(x % 2 == 0 for x in nums1)


class Solution:
    def uniformArray(self, nums1):
        return solve(nums1)
