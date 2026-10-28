"""1061. Lexicographically Smallest Equivalent String (Medium).

Specification: https://leetcode.com/problems/lexicographically-smallest-equivalent-string/description/
"""


def solve(s1: str, s2: str, baseStr: str) -> str:
    parent = list(range(26))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[max(root_a, root_b)] = min(root_a, root_b)

    for i in range(len(s1)):
        union(ord(s1[i]) - 97, ord(s2[i]) - 97)
    result = ''
    for ch in baseStr:
        result += chr(97 + find(ord(ch) - 97))
    return result


class Solution:
    def smallestEquivalentString(self, s1: str, s2: str, baseStr: str) -> str:
        return solve(s1, s2, baseStr)
