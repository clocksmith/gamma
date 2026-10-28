"""1545. Find Kth Bit in Nth Binary String (Medium).

Specification: https://leetcode.com/problems/find-kth-bit-in-nth-binary-string/description/
"""


def solve(n: int, k: int) -> str:
    text = '0'
    for _step in range(1, n):
        inverted = "".join('1' if ch == '0' else '0' for ch in reversed(text))
        text = text + '1' + inverted
    return text[k - 1]


class Solution:
    def findKthBit(self, n: int, k: int) -> str:
        return solve(n, k)
