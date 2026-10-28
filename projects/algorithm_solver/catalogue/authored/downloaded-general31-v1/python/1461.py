"""1461. Check If a String Contains All Binary Codes of Size K (Medium).

Specification: https://leetcode.com/problems/check-if-a-string-contains-all-binary-codes-of-size-k/description/
"""


def solve(s: str, k: int) -> bool:
    seen = set()
    for i in range(len(s) - k + 1):
        seen.add(s[i:i + k])
    return len(seen) == (1 << k)


class Solution:
    def hasAllCodes(self, s: str, k: int) -> bool:
        return solve(s, k)
