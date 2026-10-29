"""Hack2Hire 6a1cd98b8b879849ebc0fdaf (Find Matching Skeletons) over an INFERRED spec; qualification unknown."""


def solve(word, skeletons):
    out = []
    for skeleton in skeletons:
        hidden = None
        ok = True
        for i, ch in enumerate(skeleton):
            if ch == '-':
                if hidden is None:
                    hidden = word[i]
                elif word[i] != hidden:
                    ok = False
                    break
            elif ch != word[i]:
                ok = False
                break
        if ok:
            out.append(skeleton)
    return out


class Solution:
    def findMatchingSkeletons(self, word, skeletons):
        return solve(word, skeletons)
