"""Hack2Hire 68dc5d69dd5418be11109b00 (Spelling Bee Word Finder) over an INFERRED spec; qualification unknown."""

def solve(requiredLetter, optionalLetters, dictionary):
    required = 1 << (ord(requiredLetter) - 97)
    allowed = required
    for ch in optionalLetters:
        allowed |= 1 << (ord(ch) - 97)
    forbidden = ~allowed
    out = []
    for word in dictionary:
        if len(word) < 4:
            continue
        mask = 0
        for ch in word:
            mask |= 1 << (ord(ch) - 97)
        if mask & required and not mask & forbidden:
            out.append(word)
    return out


class Solution:
    def findValidWords(self, requiredLetter, optionalLetters, dictionary):
        return solve(requiredLetter, optionalLetters, dictionary)
