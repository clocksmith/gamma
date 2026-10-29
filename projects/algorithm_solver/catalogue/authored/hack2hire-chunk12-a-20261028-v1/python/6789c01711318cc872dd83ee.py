"""Hack2Hire 6789c01711318cc872dd83ee (Longest Valid Parentheses) over an INFERRED spec; qualification unknown."""


_RANK = {'(': 1, '[': 2, '{': 3, ')': 1, ']': 2, '}': 3}
_OPEN = {')': '(', ']': '[', '}': '{'}


def solve(s):
    pos, kind, inner = [], [], []  # open frames: position, opener, highest rank closed inside
    barrier, best = -1, 0
    for i, ch in enumerate(s):
        if ch not in _OPEN:
            pos.append(i)
            kind.append(ch)
            inner.append(0)
        elif kind and kind[-1] == _OPEN[ch] and inner[-1] <= _RANK[ch]:
            pos.pop()
            kind.pop()
            inner.pop()
            if inner:
                if inner[-1] < _RANK[ch]:
                    inner[-1] = _RANK[ch]
                start = pos[-1]
            else:
                start = barrier
            if i - start > best:
                best = i - start
        else:
            pos.clear()
            kind.clear()
            inner.clear()
            barrier = i
    return best


class Solution:
    def longestValidBrackets(self, s):
        return solve(s)
