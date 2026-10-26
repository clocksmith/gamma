"""3848. Check Digitorial Permutation."""
from __future__ import annotations
from collections import Counter


def solve(n: int) -> bool:
    """O(d) time and O(1) alphabet space; the factorial sum is invariant under all digit permutations."""
    factorials = [1] * 10
    for digit in range(1, 10):
        factorials[digit] = factorials[digit - 1] * digit
    text = str(n)
    value = sum(factorials[int(char)] for char in text)
    return Counter(text) == Counter(str(value))


class Solution:
    def isDigitorialPermutation(self, n: int) -> bool:
        return solve(n)
