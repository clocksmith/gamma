"""Hack2Hire 6a5019e9665efda9311f5903 (Streaming Stop Token, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(stream):
    out = []
    for chunk in stream:
        position = chunk.find('<END>')
        if position >= 0:
            if position > 0:
                out.append(chunk[:position])
            return out
        out.append(chunk)
    return out


class Solution:
    def truncateAtStop(self, stream):
        return solve(stream)
