"""3177. Find the Maximum Length of a Good Subsequence II.

DP by final value and allowed changes, updated in descending budget order; O(n*k) expected time, O(U*k) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> int:
    endings = {}
    best = [0] * (k + 1)
    for value in nums:
        row = endings.setdefault(value, [0] * (k + 1))
        for changes in range(k, -1, -1):
            row[changes] = max(row[changes] + 1, best[changes - 1] + 1 if changes else 1)
            best[changes] = max(best[changes], row[changes])
    return best[k]


class Solution:
    def maximumLength(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
