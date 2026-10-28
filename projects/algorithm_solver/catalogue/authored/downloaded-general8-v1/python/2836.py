"""2836. Maximize Value of Function in a Ball Passing Game (Hard).

Specification: https://leetcode.com/problems/maximize-value-of-function-in-a-ball-passing-game/description/
"""


def solve(receiver, k):
    n = len(receiver)
    m = k.bit_length()
    jump = [[0] * m for _ in range(n)]
    summ = [[0] * m for _ in range(n)]
    for i in range(n):
        jump[i][0] = receiver[i]
        summ[i][0] = receiver[i]
    for j in range(1, m):
        for i in range(n):
            mid = jump[i][j - 1]
            jump[i][j] = jump[mid][j - 1]
            summ[i][j] = summ[i][j - 1] + summ[mid][j - 1]
    ans = 0
    for i in range(n):
        total = i
        pos = i
        for j in range(m):
            if (k >> j) & 1:
                total += summ[pos][j]
                pos = jump[pos][j]
        ans = max(ans, total)
    return ans


class Solution:
    def getMaxFunctionValue(self, *args):
        return solve(*args)
