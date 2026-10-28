"""345. Reverse Vowels of a String (Easy).

Specification: https://leetcode.com/problems/reverse-vowels-of-a-string/description/
"""


VOWELS = set('aeiouAEIOU')


def solve(s: str) -> str:
    chars = list(s)
    left, right = 0, len(chars) - 1
    while left < right:
        while left < right and chars[left] not in VOWELS:
            left += 1
        while left < right and chars[right] not in VOWELS:
            right -= 1
        if left < right:
            chars[left], chars[right] = chars[right], chars[left]
            left += 1
            right -= 1
    return "".join(chars)


class Solution:
    def reverseVowels(self, s: str) -> str:
        return solve(s)
