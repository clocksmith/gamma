"""2842. Count K-Subsequences of a String With Maximum Beauty. Choose the highest character frequencies and count ties at the cutoff."""

from collections import Counter
from math import comb


def solve(s: str, k: int) -> int:
    """O(n+26 log 26) time and O(26) space. Inputs are preserved."""
    modulus = 1_000_000_007
    if k == 0:
        return 1
    frequencies = sorted(Counter(s).values(), reverse=True)
    if k > len(frequencies):
        return 0
    cutoff = frequencies[k - 1]
    greater = 0
    equal = 0
    answer = 1
    for frequency in frequencies:
        if frequency > cutoff:
            greater += 1
            answer = answer * frequency % modulus
        elif frequency == cutoff:
            equal += 1
    needed = k - greater
    return answer * comb(equal, needed) % modulus * pow(cutoff, needed, modulus) % modulus


class Solution:
    def countKSubsequencesWithMaxBeauty(self, s: str, k: int) -> int:
        return solve(s, k)
