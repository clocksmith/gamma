"""649. Dota2 Senate (Medium).

Specification: https://leetcode.com/problems/dota2-senate/description/
"""


from collections import deque


def solve(senate: str) -> str:
    n = len(senate)
    radiant = deque()
    dire = deque()
    for i, ch in enumerate(senate):
        if ch == 'R':
            radiant.append(i)
        else:
            dire.append(i)
    while radiant and dire:
        r = radiant.popleft()
        d = dire.popleft()
        if r < d:
            radiant.append(r + n)
        else:
            dire.append(d + n)
    return 'Radiant' if radiant else 'Dire'


class Solution:
    def predictPartyVictory(self, senate: str) -> str:
        return solve(senate)
