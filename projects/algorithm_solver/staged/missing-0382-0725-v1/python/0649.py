"""649. Dota2 Senate."""

from collections import deque

def solve(senate: str) -> str:
    radiant = deque(i for i, party in enumerate(senate) if party == 'R')
    dire = deque(i for i, party in enumerate(senate) if party == 'D')
    size = len(senate)
    while radiant and dire:
        r, d = radiant.popleft(), dire.popleft()
        if r < d:
            radiant.append(r + size)
        else:
            dire.append(d + size)
    return 'Radiant' if radiant else 'Dire'


class Solution:
    def predictPartyVictory(self, senate: str) -> str:
        return solve(senate)
