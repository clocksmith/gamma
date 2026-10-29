"""Hack2Hire 69a351986e73e4abccc9bf81 (Longest Consecutive Segment After Insertions) over an INFERRED spec; qualification unknown."""

def solve(queries):
    occupied, length, best, out = set(), {}, 0, []
    for p in queries:
        if p not in occupied and not (p - 1 in occupied and p + 1 in occupied):
            occupied.add(p)
            left = length[p - 1] if p - 1 in occupied else 0    # p - 1 is the right end of its run
            right = length[p + 1] if p + 1 in occupied else 0   # p + 1 is the left end of its run
            total = left + right + 1
            length[p - left] = total
            length[p + right] = total
            if total > best:
                best = total
        out.append(best)
    return out


class Solution:
    def longestSegments(self, queries):
        return solve(queries)
