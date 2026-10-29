"""Hack2Hire 6a4d62db60d5cca82da2fdda (Beam Search Decoding, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(scores, beamWidth):
    beam = [(0, 0, [])]  # (total, lexicographic rank, sequence), best first
    for row in scores:
        tokens = sorted(range(len(row)), key=lambda j: (-row[j], j))[:beamWidth]
        candidates = []
        for total, rank, seq in beam:
            for j in tokens:
                candidates.append((-(total + row[j]), rank, j, seq))
        candidates.sort(key=lambda c: (c[0], c[1], c[2]))
        kept = candidates[:beamWidth]
        order = sorted(range(len(kept)), key=lambda k: (kept[k][1], kept[k][2]))
        ranks = [0] * len(kept)
        for r, k in enumerate(order):
            ranks[k] = r
        beam = [(-c[0], ranks[k], c[3] + [c[2]]) for k, c in enumerate(kept)]
    return [seq for _, _, seq in beam]


class Solution:
    def beamSearch(self, scores, beamWidth):
        return solve(scores, beamWidth)
