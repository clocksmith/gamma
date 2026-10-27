"""354. Russian Doll Envelopes."""
from bisect import bisect_left

def solve(envelopes: list[list[int]]) -> int:
    envelopes = sorted(envelopes, key=lambda value: (value[0], -value[1]))
    tails = []
    for _, height in envelopes:
        index = bisect_left(tails, height)
        if index == len(tails):
            tails.append(height)
        else:
            tails[index] = height
    return len(tails)

class Solution:
    def maxEnvelopes(self, envelopes: list[list[int]]) -> int:
        return solve(envelopes)
