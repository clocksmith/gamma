"""Hack2Hire 68e1734e0fdcf62632c38cdc (Find Valid Sock Pairs, variant 2). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(ids, colors, feet):
    lefts, rights = {}, {}
    for sock_id, color, foot in zip(ids, colors, feet):
        (lefts if foot == 'left' else rights).setdefault(color, []).append(sock_id)
    pairs = []
    for color, left_ids in lefts.items():
        right_ids = sorted(rights.get(color, []))
        for left_id, right_id in zip(sorted(left_ids), right_ids):
            pairs.append([left_id, right_id])
    pairs.sort(key=lambda pair: pair[0])
    return pairs


class Solution:
    def findSockPairs(self, ids, colors, feet):
        return solve(ids, colors, feet)
