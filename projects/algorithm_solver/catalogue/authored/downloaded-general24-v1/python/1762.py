"""1762. Buildings With an Ocean View (Medium).

Specification: https://leetcode.com/problems/buildings-with-an-ocean-view/description/
"""


def solve(heights: list[int]) -> list[int]:
    result = []
    tallest = 0
    for i in range(len(heights) - 1, -1, -1):
        if heights[i] > tallest:
            result.append(i)
            tallest = heights[i]
    return result[::-1]


class Solution:
    def findBuildings(self, heights: list[int]) -> list[int]:
        return solve(heights)
