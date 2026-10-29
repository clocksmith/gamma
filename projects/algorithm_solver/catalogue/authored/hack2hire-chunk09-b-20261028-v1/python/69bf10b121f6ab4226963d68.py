"""Hack2Hire 69bf10b121f6ab4226963d68 (Chunk a List of Lists) over an INFERRED spec; qualification unknown."""


def solve(data, size):
    out = []
    buffer = []
    for inner in data:
        for value in inner:
            buffer.append(value)
            if len(buffer) == size:
                out.append(buffer)
                buffer = []
    if buffer:
        out.append(buffer)
    return out


class Solution:
    def rechunk(self, data, size):
        return solve(data, size)
