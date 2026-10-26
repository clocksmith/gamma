"""1879. Minimum XOR Sum of Two Arrays."""


def solve(nums1: list[int], nums2: list[int]) -> int:
    """Assignment DP over used positions; O(n*2^n) time and O(2^n) space. Inputs are preserved."""
    size = len(nums1)
    count = 1 << size
    best = [float('inf')] * count
    best[0] = 0
    for mask in range(count - 1):
        index = mask.bit_count()
        for other in range(size):
            bit = 1 << other
            if mask & bit == 0:
                following = mask | bit
                best[following] = min(best[following], best[mask] + (nums1[index] ^ nums2[other]))
    return best[-1]


class Solution:
    def minimumXORSum(self, nums1: list[int], nums2: list[int]) -> int:
        return solve(nums1, nums2)
