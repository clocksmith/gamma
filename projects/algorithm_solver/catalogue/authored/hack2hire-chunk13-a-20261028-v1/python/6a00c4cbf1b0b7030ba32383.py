"""Hack2Hire 6a00c4cbf1b0b7030ba32383 (Rank Songs by Popularity) over an INFERRED spec; qualification unknown."""


def solve(pref):
    m = len(pref[0])
    votes = [[0] * m for _ in range(m)]  # votes[song][position], negated later for a descending sort
    for p in pref:
        for pos, song in enumerate(p):
            votes[song][pos] += 1
    keys = [[-c for c in votes[s]] + [s] for s in range(m)]
    return sorted(range(m), key=lambda s: keys[s])


class Solution:
    def rankSongs(self, pref):
        return solve(pref)
