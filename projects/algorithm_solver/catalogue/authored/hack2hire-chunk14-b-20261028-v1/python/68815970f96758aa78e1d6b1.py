"""Hack2Hire 68815970f96758aa78e1d6b1 (Wildcard Search) over an INFERRED spec; qualification unknown."""


def find(text, piece, start):
    m = len(piece)
    if m == 0:
        return start if start <= len(text) else -1
    fail = [0] * m
    k = 0
    for i in range(1, m):
        while k and piece[i] != piece[k]:
            k = fail[k - 1]
        if piece[i] == piece[k]:
            k += 1
        fail[i] = k
    k = 0
    for i in range(start, len(text)):
        while k and text[i] != piece[k]:
            k = fail[k - 1]
        if text[i] == piece[k]:
            k += 1
            if k == m:
                return i - m + 1
    return -1


def solve(pattern, str):
    text = str
    pieces = pattern.split('*')
    first = find(text, pieces[0], 0)
    if first < 0 or len(pieces) == 1:
        return first
    pos = first + len(pieces[0])
    for piece in pieces[1:]:
        if piece:
            at = find(text, piece, pos)
            if at < 0:
                return -1
            pos = at + len(piece)
    return first


class Solution:
    def wildcardSearch(self, pattern, str):
        return solve(pattern, str)
