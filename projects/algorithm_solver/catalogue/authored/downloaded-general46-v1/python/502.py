"""502. IPO (Hard).

Specification: https://leetcode.com/problems/ipo/description/
"""


def solve(k: int, w: int, profits: list[int], capital: list[int]) -> int:
    projects = sorted(zip(capital, profits))
    current = w
    index = 0
    affordable = []
    for _step in range(k):
        while index < len(projects) and projects[index][0] <= current:
            affordable.append(projects[index][1])
            index += 1
        if not affordable:
            break
        affordable.sort(reverse=True)
        current += affordable.pop(0)
    return current


class Solution:
    def findMaximizedCapital(self, k: int, w: int, profits: list[int], capital: list[int]) -> int:
        return solve(k, w, profits, capital)
