"""Hack2Hire 6760ef452f1ff3d3c88bf915 (Smallest Lexicographical Palindrome) over an INFERRED spec; qualification unknown."""


def solve(s):
    letters = [chr(c) for c in range(97, 123)]
    counts = [s.count(ch) for ch in letters]
    half = ''.join(ch * (c // 2) for ch, c in zip(letters, counts))
    middle = ''.join(ch for ch, c in zip(letters, counts) if c % 2)
    return half + middle + half[::-1]


class Solution:
    def smallestPalindrome(self, s):
        return solve(s)
