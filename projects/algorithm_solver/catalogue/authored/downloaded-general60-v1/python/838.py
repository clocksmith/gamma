"""838. Push Dominoes (Medium).

Specification: https://leetcode.com/problems/push-dominoes/description/
"""


def solve(dominoes: str) -> str:
    n = len(dominoes)
    forces = [0] * n
    force = 0
    for i, ch in enumerate(dominoes):
        if ch == 'R':
            force = n
        elif ch == 'L':
            force = 0
        else:
            force = max(force - 1, 0)
        forces[i] += force
    force = 0
    for i in range(n - 1, -1, -1):
        ch = dominoes[i]
        if ch == 'L':
            force = n
        elif ch == 'R':
            force = 0
        else:
            force = max(force - 1, 0)
        forces[i] -= force
    result = ''
    for value in forces:
        result += 'R' if value > 0 else 'L' if value < 0 else '.'
    return result


class Solution:
    def pushDominoes(self, dominoes: str) -> str:
        return solve(dominoes)
