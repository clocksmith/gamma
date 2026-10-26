"""3842. Toggle Light Bulbs (Easy).

Specification: https://leetcode.com/problems/toggle-light-bulbs/description/
"""


def solve(bulbs: list[int]) -> list[int]:
    """O(n + 100) time, O(100) space; preserve bulbs and return lit labels in ascending order."""
    lit = [False] * 101
    for bulb in bulbs:
        lit[bulb] = not lit[bulb]
    result = []
    for bulb in range(1, 101):
        if lit[bulb]:
            result.append(bulb)
    return result


class Solution:
    def toggleLightBulbs(self, bulbs: list[int]) -> list[int]:
        return solve(bulbs)
