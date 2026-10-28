"""3210. Find the Encrypted String (Easy).

Specification: https://leetcode.com/problems/find-the-encrypted-string/description/
"""


def solve(s: str, k: int) -> str:
    n = len(s)
    return ''.join(s[(i + k) % n] for i in range(n))


class Solution:
    def getEncryptedString(self, s, k):
        return solve(s, k)
