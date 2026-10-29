"""Hack2Hire 67707837366afdc1233e4ff7 (Find Special Sequence Pairs) over an INFERRED spec; qualification unknown."""
COMPLEMENT = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}


def solve(sequences):
    seen, pairs = {}, 0
    for s in sequences:
        partner = ''.join(COMPLEMENT[ch] for ch in reversed(s))
        pairs += seen.get(partner, 0)
        seen[s] = seen.get(s, 0) + 1
    return pairs


class Solution:
    def countSpecialPairs(self, sequences):
        return solve(sequences)
