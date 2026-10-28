"""3335. Total Characters in String After Transformations I (Medium).

Specification: https://leetcode.com/problems/total-characters-in-string-after-transformations-i/description/
"""


def solve(s: str, t: int) -> int:
    MOD = 1000000007
    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - 97] += 1
    for _ in range(t):
        nxt = [0] * 26
        z = counts[25]
        nxt[0] = (nxt[0] + z) % MOD
        nxt[1] = (nxt[1] + z) % MOD
        for i in range(25):
            nxt[i + 1] = (nxt[i + 1] + counts[i]) % MOD
        counts = nxt
    return sum(counts) % MOD


class Solution:
    def lengthAfterTransformations(self, s: str, t: int) -> int:
        return solve(s, t)
