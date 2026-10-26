"""2293. Min Max Game (Easy).

Specification: https://leetcode.com/problems/min-max-game/description/
"""


def solve(nums: list[int]) -> int:
    """O(n) time, O(n) space; reduce alternating min/max pairs on copies; preserve nums."""
    current = list(nums)
    while len(current) > 1:
        next_values = []
        for index in range(len(current) // 2):
            first = current[index * 2]
            second = current[index * 2 + 1]
            next_values.append(min(first, second) if index % 2 == 0 else max(first, second))
        current = next_values
    return current[0]


class Solution:
    def minMaxGame(self, nums: list[int]) -> int:
        return solve(nums)
