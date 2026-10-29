"""Hack2Hire 67e45b2850b60b77022f382e (Word Pattern Match) over an INFERRED spec; qualification unknown."""


def solve(pattern, words):
    result = []
    for word in words:
        if len(word) != len(pattern):
            result.append(False)
            continue
        forward = {}
        backward = {}
        ok = True
        for a, b in zip(pattern, word):
            x = forward.get(a)
            y = backward.get(b)
            if x is None and y is None:
                forward[a] = b
                backward[b] = a
            elif x != b or y != a:
                ok = False
                break
        result.append(ok)
    return result


class Solution:
    def matchWords(self, pattern, words):
        return solve(pattern, words)
