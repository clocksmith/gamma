"""Hack2Hire 687e9cfe7bd121d1f502daa2 (Block-Based String Assembly) over an INFERRED spec; qualification unknown."""


def solve(blocks, target):
    if len(target) > len(blocks):
        return False
    holders = {}
    for b, block in enumerate(blocks):
        for letter in set(block):
            holders.setdefault(letter, []).append(b)
    owner = [-1] * len(blocks)

    def augment(position, seen):
        for b in holders.get(target[position], ()):
            if not seen[b]:
                seen[b] = True
                if owner[b] < 0 or augment(owner[b], seen):
                    owner[b] = position
                    return True
        return False

    for position in range(len(target)):
        if not augment(position, [False] * len(blocks)):
            return False
    return True


class Solution:
    def canAssemble(self, blocks, target):
        return solve(blocks, target)
