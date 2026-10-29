"""Hack2Hire 688bd40e3867670cfb894186 (String Replacement) over an INFERRED spec; qualification unknown."""

def solve(source, target, replacement):
    m = len(target)
    fail = [0] * m
    k = 0
    for i in range(1, m):
        while k and target[i] != target[k]:
            k = fail[k - 1]
        if target[i] == target[k]:
            k += 1
        fail[i] = k
    starts = []
    k = 0
    for i, ch in enumerate(source):
        while k and ch != target[k]:
            k = fail[k - 1]
        if ch == target[k]:
            k += 1
        if k == m:
            starts.append(i - m + 1)
            k = 0
    out = []
    i = 0
    nxt = 0
    n = len(source)
    while i < n:
        if nxt < len(starts) and starts[nxt] == i:
            out.append(replacement)
            i += m
            nxt += 1
        else:
            out.append(source[i])
            i += 1
    return ''.join(out)


class Solution:
    def replaceAll(self, source, target, replacement):
        return solve(source, target, replacement)
