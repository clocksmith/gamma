"""2124. Check if All A's Appears Before All B's (Easy).

Specification: https://leetcode.com/problems/check-if-all-as-appears-before-all-bs/description/
"""


def solve(s: str) -> bool:
    """O(n) time, O(1) space; reject an a after any b."""
    seen_b = False
    for character in s:
        if character == 'b':
            seen_b = True
        elif seen_b:
            return False
    return True


class Solution:
    def checkString(self, s: str) -> bool:
        return solve(s)
