"""Hack2Hire 6a480ba0ca956256d786d277 (Segment Sequence Reconstruction, variant 2 of 3) over an INFERRED spec; qualification unknown."""


def solve(segments):
    by_start = {s[0]: s for s in segments}
    ends = {s[1] for s in segments}
    heads = [s for s in segments if s[0] not in ends]
    if len(heads) != 1:
        return ''
    parts = []
    segment = heads[0]
    while segment is not None:
        parts.append(segment[2])
        segment = by_start.get(segment[1])
    return ''.join(parts) if len(parts) == len(segments) else ''


class Solution:
    def reconstructSequence(self, segments):
        return solve(segments)
