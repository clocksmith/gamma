"""Hack2Hire 6a480bbbca956256d786d279 (Segment Sequence Reconstruction, variant 3 of 3) over an INFERRED spec; qualification unknown."""


def solve(segments):
    by_start = {s[0]: s for s in segments}
    ends = {s[1] for s in segments}
    heads = sorted(s[0] for s in segments if s[0] not in ends)
    out = []
    for head in heads:
        parts = []
        segment = by_start[head]
        while segment is not None:
            parts.append(segment[2])
            segment = by_start.get(segment[1])
        out.append(''.join(parts))
    return out


class Solution:
    def reconstructAllSequences(self, segments):
        return solve(segments)
