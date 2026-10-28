"""187. Repeated DNA Sequences (Medium).

Specification: https://leetcode.com/problems/repeated-dna-sequences/description/
"""


def solve(s: str) -> list[str]:
    seen = set()
    repeated = set()
    for i in range(len(s) - 9):
        part = s[i:i + 10]
        if part in seen:
            repeated.add(part)
        else:
            seen.add(part)
    return sorted(repeated)


class Solution:
    def findRepeatedDnaSequences(self, s: str) -> list[str]:
        return solve(s)
