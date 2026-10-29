"""Hack2Hire 68d9756679db2fbcd7d7db74 (Equal Frequency After One Deletion) over an INFERRED spec; qualification unknown."""


def solve(s):
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    freq = {}
    for c in counts.values():
        freq[c] = freq.get(c, 0) + 1
    if len(freq) == 1:
        return True
    if len(freq) > 2:
        return False
    (low, nlow), (high, nhigh) = sorted(freq.items())
    return (low == 1 and nlow == 1) or (high == low + 1 and nhigh == 1)


class Solution:
    def equalFrequency(self, s):
        return solve(s)
