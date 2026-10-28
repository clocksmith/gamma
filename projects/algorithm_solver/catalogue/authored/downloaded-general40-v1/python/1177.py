"""1177. Can Make Palindrome from Substring (Medium).

Specification: https://leetcode.com/problems/can-make-palindrome-from-substring/description/
"""


def solve(s: str, queries: list[list[int]]) -> list[bool]:
    prefix = [[0] * 26]
    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - 97] += 1
        prefix.append(counts[:])
    result = []
    for left, right, k in queries:
        odd = 0
        for letter in range(26):
            if (prefix[right + 1][letter] - prefix[left][letter]) % 2 == 1:
                odd += 1
        result.append(odd // 2 <= k)
    return result


class Solution:
    def canMakePaliQueries(self, s: str, queries: list[list[int]]) -> list[bool]:
        return solve(s, queries)
