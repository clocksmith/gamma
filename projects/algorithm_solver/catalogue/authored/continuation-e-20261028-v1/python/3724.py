def solve(nums1, nums2):
    z = nums2[-1]
    base = 1
    extra = float('inf')
    for x, y in zip(nums1, nums2):
        base += abs(x - y)
        extra = min(extra, max(min(x, y) - z, z - max(x, y), 0))
    return base + extra


class Solution:
    def minOperations(self, nums1, nums2):
        return solve(nums1, nums2)
