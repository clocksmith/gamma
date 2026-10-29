"""Hack2Hire 68dee4164b499ddb216af5ec (Find Valid Sock Pairs, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(ids, colors, feet):
    lefts, rights = {}, {}
    for color, foot in zip(colors, feet):
        side = lefts if foot == 'left' else rights
        side[color] = side.get(color, 0) + 1
    return sum(min(count, rights.get(color, 0)) for color, count in lefts.items())


class Solution:
    def countSockPairs(self, ids, colors, feet):
        return solve(ids, colors, feet)
