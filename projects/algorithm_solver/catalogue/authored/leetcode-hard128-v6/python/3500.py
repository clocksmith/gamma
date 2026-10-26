"""3500. Minimum Cost to Divide Array Into Subarrays.

Charge each segment start for all later cost weights, eliminating the segment-count state; O(n^2) time and O(n) space. Inputs are preserved.
"""

def solve(nums: list[int], cost: list[int], k: int) -> int:
    n = len(nums)
    values, weights = [0], [0]
    for value, weight in zip(nums, cost):
        values.append(values[-1] + value)
        weights.append(weights[-1] + weight)
    best = [0] * (n + 1)
    for start in range(n - 1, -1, -1):
        surcharge = k * (weights[n] - weights[start])
        best[start] = min(values[end] * (weights[end] - weights[start]) + surcharge + best[end]
                          for end in range(start + 1, n + 1))
    return best[0]


class Solution:
    def minimumCost(self, nums: list[int], cost: list[int], k: int) -> int:
        return solve(nums, cost, k)
