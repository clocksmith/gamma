"""3502. Minimum Cost to Reach Every Position (Easy).

Specification: https://leetcode.com/problems/minimum-cost-to-reach-every-position/description/
"""


def solve(cost: list[int]) -> list[int]:
    """O(n) time and output space; a prefix minimum permits free backward swaps."""
    result = []
    cheapest = float('inf')
    for value in cost:
        cheapest = min(cheapest, value)
        result.append(cheapest)
    return result


class Solution:
    def minCosts(self, cost: list[int]) -> list[int]:
        return solve(cost)
