"""784. Letter Case Permutation: expand lowercase and uppercase choices for each ASCII letter."""


def solve(s: str) -> list[str]:
    """O(n * 2^l) time and output space for l letters; inputs are read-only."""
    variants = ['']
    for char in s:
        if '0' <= char <= '9':
            variants = [prefix + char for prefix in variants]
        else:
            lower, upper = char.lower(), char.upper()
            variants = [prefix + choice for prefix in variants for choice in (lower, upper)]
    return variants


class Solution:
    def letterCasePermutation(self, s: str) -> list[str]:
        return solve(s)
