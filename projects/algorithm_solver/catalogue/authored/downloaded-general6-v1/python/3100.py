"""3100. Water Bottles II (Easy).

Specification: https://leetcode.com/problems/water-bottles-ii/description/
"""


def solve(num_bottles: int, num_exchange: int) -> int:
    answer = num_bottles
    while num_bottles >= num_exchange:
        num_bottles = num_bottles - num_exchange + 1
        num_exchange += 1
        answer += 1
    return answer


class Solution:
    def maxBottlesDrunk(self, num_bottles: int, num_exchange: int) -> int:
        return solve(num_bottles, num_exchange)
