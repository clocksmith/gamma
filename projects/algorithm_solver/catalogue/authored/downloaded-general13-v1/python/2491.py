"""2491. Divide Players Into Teams of Equal Skill (Medium).

Specification: https://leetcode.com/problems/divide-players-into-teams-of-equal-skill/description/
"""


def solve(skill):
    s = sorted(skill)
    if len(s) % 2 == 1:
        return -1
    target = s[0] + s[-1]
    total = 0
    for i in range(len(s) // 2):
        if s[i] + s[-1 - i] != target:
            return -1
        total += s[i] * s[-1 - i]
    return total


class Solution:
    def dividePlayers(self, skill):
        return solve(skill)
