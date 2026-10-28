"""Original frontend 3836 variant; qualification unknown."""

def solve(nums1, nums2, k):
    width = len(nums2)
    impossible = -10**30
    previous = [[0] + [impossible] * k for _ in range(width + 1)]
    for first in nums1:
        current = [[0] + [impossible] * k for _ in range(width + 1)]
        for j, second in enumerate(nums2, 1):
            for count in range(1, k + 1):
                best = max(previous[j][count], current[j - 1][count])
                diagonal = previous[j - 1][count - 1]
                if diagonal != impossible:
                    best = max(best, diagonal + first * second)
                current[j][count] = best
        previous = current
    return previous[-1][k]


class Solution:
    def maxScore(self, nums1, nums2, k):
        return solve(nums1, nums2, k)
