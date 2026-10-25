"""1400. Construct K Palindrome Strings: bound the number of required palindrome centers."""


def solve(s: str, k: int) -> bool:
    """O(n) time and O(1) auxiliary space for lowercase English letters; inputs are read-only."""
    if k > len(s):
        return False
    frequencies = [0] * 26
    for character in s:
        frequencies[ord(character) - ord("a")] += 1
    odd_count = sum(frequency % 2 for frequency in frequencies)
    return odd_count <= k


class Solution:
    def canConstruct(self, s: str, k: int) -> bool:
        return solve(s, k)
