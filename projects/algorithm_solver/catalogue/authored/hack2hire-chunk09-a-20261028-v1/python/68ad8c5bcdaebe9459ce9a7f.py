"""Hack2Hire 68ad8c5bcdaebe9459ce9a7f (Validate  Playlist Sequence) over an INFERRED spec; qualification unknown."""


def solve(numSongs, sequence):
    n = numSongs
    last = {}
    cover = [0] * (n + 1)
    arcs = 0
    for i, song in enumerate(sequence):
        j = last.get(song)
        last[song] = i
        if j is None or i - j >= n:
            continue
        arcs += 1
        lo, hi = (j + 1) % n, i % n  # allowed cut residues lo..hi, wrapping
        if lo <= hi:
            cover[lo] += 1
            cover[hi + 1] -= 1
        else:
            cover[lo] += 1
            cover[n] -= 1
            cover[0] += 1
            cover[hi + 1] -= 1
    if arcs == 0:
        return True
    running = 0
    for r in range(n):
        running += cover[r]
        if running == arcs:
            return True
    return False


class Solution:
    def isShuffleSequence(self, numSongs, sequence):
        return solve(numSongs, sequence)
