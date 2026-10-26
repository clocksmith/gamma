"""800. Similar RGB Color (Easy).

Specification: https://leetcode.com/problems/similar-rgb-color/description/
"""


def solve(color: str) -> str:
    """O(1) time and space; round each hexadecimal channel to its nearest multiple of 17."""
    result = ['#']
    for index in range(1, len(color), 2):
        channel = int(color[index:index + 2], 16)
        digit = format((channel + 8) // 17, 'x')
        result.extend((digit, digit))
    return ''.join(result)


class Solution:
    def similarRGB(self, color: str) -> str:
        return solve(color)
