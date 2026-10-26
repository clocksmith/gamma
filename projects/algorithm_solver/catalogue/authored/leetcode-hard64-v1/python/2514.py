"""2514. Count Anagrams: per-word multinomials with one modular inverse."""

from collections import Counter


def solve(s: str) -> int:
    """O(n + log MOD) time and O(n) auxiliary space for split words. Inputs are preserved."""
    modulus = 1_000_000_007
    numerator = 1
    denominator = 1
    for word in s.split(' '):
        for factor in range(2, len(word) + 1):
            numerator = numerator * factor % modulus
        for count in Counter(word).values():
            for factor in range(2, count + 1):
                denominator = denominator * factor % modulus
    return numerator * pow(denominator, modulus - 2, modulus) % modulus


class Solution:
    def countAnagrams(self, s: str) -> int:
        return solve(s)
