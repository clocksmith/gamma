"""789. Escape The Ghosts (Medium).

Specification: https://leetcode.com/problems/escape-the-ghosts/description/
"""


def solve(ghosts: list[list[int]], target: list[int]) -> bool:
    player = abs(target[0]) + abs(target[1])
    for gx, gy in ghosts:
        if abs(gx - target[0]) + abs(gy - target[1]) <= player:
            return False
    return True


class Solution:
    def escapeGhosts(self, ghosts: list[list[int]], target: list[int]) -> bool:
        return solve(ghosts, target)
