"""Hack2Hire 6a4809cfca956256d786d255 (Segment Sequence Reconstruction, variant 1 of 3) over an INFERRED spec; qualification unknown."""


def solve(segments):
    by_start = {s[0]: s for s in segments}
    ends = {s[1] for s in segments}
    segment = next(s for s in segments if s[0] not in ends)
    parts = []
    while segment is not None:
        parts.append(segment[2])
        segment = by_start.get(segment[1])
    return ''.join(parts)


class Solution:
    def reconstructSequence(self, segments):
        return solve(segments)
