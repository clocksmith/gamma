"""846. Hand of Straights (Medium).

Specification: https://leetcode.com/problems/hand-of-straights/description/
"""


def solve(hand: list[int], groupSize: int) -> bool:
    if len(hand) % groupSize != 0:
        return False
    counts = {}
    for value in hand:
        counts[value] = counts.get(value, 0) + 1
    for start in sorted(counts):
        need = counts[start]
        if need == 0:
            continue
        for value in range(start, start + groupSize):
            if counts.get(value, 0) < need:
                return False
            counts[value] -= need
    return True


class Solution:
    def isNStraightHand(self, hand: list[int], groupSize: int) -> bool:
        return solve(hand, groupSize)
