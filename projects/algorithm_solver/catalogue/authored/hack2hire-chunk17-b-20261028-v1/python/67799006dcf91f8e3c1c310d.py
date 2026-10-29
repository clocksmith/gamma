"""Hack2Hire 67799006dcf91f8e3c1c310d (Wildcard Matching) over an INFERRED spec; qualification unknown."""


def solve(s, p):
    if '*' not in p:
        return s == p
    pieces = p.split('*')
    first = pieces[0]
    last = pieces[-1]
    if len(first) + len(last) > len(s) or not s.startswith(first) or not s.endswith(last):
        return False
    position = len(first)
    end = len(s) - len(last)
    for piece in pieces[1:-1]:
        if not piece:
            continue
        found = s.find(piece, position, end)
        if found < 0:
            return False
        position = found + len(piece)
    return True


class Solution:
    def isMatch(self, s, p):
        return solve(s, p)
