"""Hack2Hire 67eb157b4c9bb801bfd0ef6f (Offset Commit) over an INFERRED spec; qualification unknown."""

def solve(offsets):
    done = set()
    nxt = 0
    out = []
    for x in offsets:
        done.add(x)
        start = nxt
        while nxt in done:
            done.discard(nxt)
            nxt += 1
        out.append(nxt - 1 if nxt > start else -1)
    return out


class Solution:
    def commitOffsets(self, offsets):
        return solve(offsets)
