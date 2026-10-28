"""38. Count and Say (Medium).

Specification: https://leetcode.com/problems/count-and-say/description/
"""


def solve(n: int) -> str:
    current = '1'
    for _step in range(1, n):
        nxt = ''
        count = 1
        for i, ch in enumerate(current):
            if i + 1 < len(current) and current[i + 1] == ch:
                count += 1
            else:
                nxt += str(count) + ch
                count = 1
        current = nxt
    return current


class Solution:
    def countAndSay(self, n: int) -> str:
        return solve(n)
