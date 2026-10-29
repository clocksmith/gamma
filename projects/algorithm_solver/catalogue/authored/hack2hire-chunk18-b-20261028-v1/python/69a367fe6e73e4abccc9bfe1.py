"""Hack2Hire 69a367fe6e73e4abccc9bfe1 (Next Consonant Transformation) over an INFERRED spec; qualification unknown."""


_VOWELS = 'aeiou'
_CONSONANTS = [chr(c) for c in range(97, 123) if chr(c) not in _VOWELS]
_TABLE = str.maketrans({c: _CONSONANTS[(i + 1) % len(_CONSONANTS)] for i, c in enumerate(_CONSONANTS)})


def solve(s):
    return s.translate(_TABLE)


class Solution:
    def transformString(self, s):
        return solve(s)
