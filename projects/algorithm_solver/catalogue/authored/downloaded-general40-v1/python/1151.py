"""1151. Minimum Swaps to Group All 1's Together (Medium).

Specification: https://leetcode.com/problems/minimum-swaps-to-group-all-1s-together/description/
"""


def solve(data: list[int]) -> int:
    total = sum(data)
    if total <= 1:
        return 0
    zeros = sum(1 for x in data[:total] if x == 0)
    best = zeros
    for i in range(total, len(data)):
        if data[i] == 0:
            zeros += 1
        if data[i - total] == 0:
            zeros -= 1
        best = min(best, zeros)
    return best


class Solution:
    def minSwaps(self, data: list[int]) -> int:
        return solve(data)
