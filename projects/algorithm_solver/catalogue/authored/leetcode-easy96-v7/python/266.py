"""266. Palindrome Permutation (Easy).

Specification: https://leetcode.com/problems/palindrome-permutation/description/
"""


def solve(s: str) -> bool:
    """O(n) expected time, O(a) space for distinct characters; at most one odd count."""
    odd = set()
    for character in s:
        if character in odd:
            odd.remove(character)
        else:
            odd.add(character)
    return len(odd) <= 1


class Solution:
    def canPermutePalindrome(self, s: str) -> bool:
        return solve(s)
