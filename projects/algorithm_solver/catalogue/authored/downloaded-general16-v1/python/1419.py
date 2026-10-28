"""1419. Minimum Number of Frogs Croaking (Medium).

Specification: https://leetcode.com/problems/minimum-number-of-frogs-croaking/description/
"""


def solve(croakOfFrogs):
    order = {"c": 0, "r": 1, "o": 2, "a": 3, "k": 4}
    counts = [0, 0, 0, 0, 0]
    active = 0
    best = 0
    for ch in croakOfFrogs:
        if ch not in order:
            return -1
        stage = order[ch]
        if stage > 0 and counts[stage] >= counts[stage - 1]:
            return -1
        counts[stage] += 1
        if stage == 0:
            active += 1
            best = max(best, active)
        if stage == 4:
            active -= 1
    if active != 0:
        return -1
    if any(counts[i] != counts[0] for i in range(1, 5)):
        return -1
    return best


class Solution:
    def minNumberOfFrogs(self, croakOfFrogs):
        return solve(croakOfFrogs)
