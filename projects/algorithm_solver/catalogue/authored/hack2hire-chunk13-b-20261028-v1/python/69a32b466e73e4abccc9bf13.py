"""Hack2Hire 69a32b466e73e4abccc9bf13 (Reverse Middle of Vowel Words) over an INFERRED spec; qualification unknown."""


_VOWELS = frozenset('aeiouAEIOU')


def solve(text):
    out = []
    for word in text:
        if len(word) >= 2 and word[0] in _VOWELS and word[-1] in _VOWELS:
            out.append(word[0] + word[-2:0:-1] + word[-1])
        else:
            out.append(word)
    return out


class Solution:
    def reverseVowelWordMiddles(self, text):
        return solve(text)
