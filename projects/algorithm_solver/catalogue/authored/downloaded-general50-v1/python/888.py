"""888. Fair Candy Swap (Easy).

Specification: https://leetcode.com/problems/fair-candy-swap/description/
"""


def solve(aliceSizes: list[int], bobSizes: list[int]) -> list[int]:
    sum_a = sum(aliceSizes)
    sum_b = sum(bobSizes)
    if (sum_a - sum_b) % 2 != 0:
        return []
    diff = (sum_a - sum_b) // 2
    bob_set = set(bobSizes)
    for a in aliceSizes:
        if a - diff in bob_set:
            return [a, a - diff]
    return []


class Solution:
    def fairCandySwap(self, aliceSizes: list[int], bobSizes: list[int]) -> list[int]:
        return solve(aliceSizes, bobSizes)
