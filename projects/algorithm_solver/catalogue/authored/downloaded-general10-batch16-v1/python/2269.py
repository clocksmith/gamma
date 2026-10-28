"""2269. Find the K-Beauty of a Number (Easy).

Specification: https://leetcode.com/problems/find-the-k-beauty-of-a-number/description/
"""


def solve(num: int, k: int) -> int:
    s = str(num)
    count = 0
    for i in range(len(s) - k + 1):
        v = int(s[i:i + k])
        if v != 0 and num % v == 0:
            count += 1
    return count


class Solution:
    def divisorSubstrings(self, num, k) -> object:
        return solve(num, k)
