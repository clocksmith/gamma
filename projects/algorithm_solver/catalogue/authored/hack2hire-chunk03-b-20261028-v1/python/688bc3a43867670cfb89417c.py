"""Hack2Hire 688bc3a43867670cfb89417c (Phone Number Word Matching) over an INFERRED spec; qualification unknown."""

DIGIT = {letter: str(d) for d, letters in enumerate(['', '', 'abc', 'def', 'ghi', 'jkl', 'mno', 'pqrs', 'tuv', 'wxyz']) for letter in letters}


def solve(knownWords, phoneNumber):
    return [w for w in knownWords if len(w) == len(phoneNumber) and ''.join(DIGIT[ch] for ch in w) == phoneNumber]


class Solution:
    def matchWords(self, knownWords, phoneNumber):
        return solve(knownWords, phoneNumber)
