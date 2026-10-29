"""Hack2Hire 6a501a01665efda9311f5906 (Streaming Stop Token, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(stream):
    position = ''.join(stream).find('<END>')
    if position < 0:
        return list(stream)
    out = []
    start = 0
    for chunk in stream:
        if start <= position < start + len(chunk):
            if position > start:
                out.append(chunk[:position - start])
            return out
        out.append(chunk)
        start += len(chunk)
    return out


class Solution:
    def truncateAtSplitStop(self, stream):
        return solve(stream)
