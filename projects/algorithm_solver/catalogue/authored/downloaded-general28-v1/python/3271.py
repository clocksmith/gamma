"""3271. Hash Divided String (Medium).

Specification: https://leetcode.com/problems/hash-divided-string/description/
"""


def solve(s: str, k: int) -> str:
    out = []
    for start in range(0, len(s), k):
        total = sum(ord(ch) - 97 for ch in s[start:start + k])
        out.append(chr(97 + total % 26))
    return ''.join(out)


class Solution:
    def stringHash(self, s: str, k: int) -> str:
        return solve(s, k)
