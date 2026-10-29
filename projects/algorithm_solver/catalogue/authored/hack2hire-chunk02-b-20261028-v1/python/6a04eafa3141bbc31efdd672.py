"""Original Hack2Hire 6a04eafa3141bbc31efdd672 variant over an INFERRED specification; qualification unknown."""


def solve(data, updates):
    flips = [0] * (len(data) + 1)
    for left, right in updates:
        flips[left - 1] ^= 1
        flips[right] ^= 1
    out, parity = [], 0
    for i, value in enumerate(data):
        parity ^= flips[i]
        out.append(-value if parity else value)
    return out


class Solution:
    def applyRangeNegations(self, data, updates):
        return solve(data, updates)
