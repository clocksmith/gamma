"""3077. Maximum Strength of K Disjoint Subarrays.

Descending-count DP distinguishes an open last interval from completed prefixes; O(n*k) time and O(k) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    best = [0] + [float('-inf')] * k
    ending = [float('-inf')] * (k + 1)
    for position, value in enumerate(nums, 1):
        for count in range(min(k, position), 0, -1):
            weight = (k - count + 1) * (1 if count % 2 else -1)
            ending[count] = max(ending[count], best[count - 1]) + weight * value
            best[count] = max(best[count], ending[count])
    return best[k]


class Solution:
    def maximumStrength(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
