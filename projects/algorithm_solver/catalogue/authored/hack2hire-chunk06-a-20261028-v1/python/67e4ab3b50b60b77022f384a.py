"""Hack2Hire 67e4ab3b50b60b77022f384a (Find Shortest Unique Prefix) over an INFERRED spec; qualification unknown."""


def common(a, b):
    k, limit = 0, min(len(a), len(b))
    while k < limit and a[k] == b[k]:
        k += 1
    return k


def solve(words):
    n = len(words)
    order = sorted(range(n), key=words.__getitem__)
    need = [1] * n
    for x, y in zip(order, order[1:]):
        k = common(words[x], words[y]) + 1
        if k > need[x]:
            need[x] = k
        if k > need[y]:
            need[y] = k
    return [w[:need[i]] for i, w in enumerate(words)]


class Solution:
    def shortestUniquePrefix(self, words):
        return solve(words)
