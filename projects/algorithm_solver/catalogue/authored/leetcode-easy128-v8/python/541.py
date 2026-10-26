"""541. Reverse String II (Easy).

Specification: https://leetcode.com/problems/reverse-string-ii/description/
"""


def solve(s: str, k: int) -> str:
    """O(n) time and space; reverse the first k characters in each 2k block."""
    result = list(s)
    for start in range(0, len(result), 2 * k):
        left, right = start, min(start + k, len(result)) - 1
        while left < right:
            result[left], result[right] = result[right], result[left]
            left += 1
            right -= 1
    return ''.join(result)


class Solution:
    def reverseStr(self, s: str, k: int) -> str:
        return solve(s, k)
