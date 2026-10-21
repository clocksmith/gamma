def f(a, b, c, d):
    e = [c] * b
    for i in range(a):
        g = c
        for j in range(b):
            e[j] = g = d(i, j, e[j], g)
    return e[-1]
class Solution:

    def minPathSum(self, a):
        return f(len(a), len(a[0]), float('inf'), lambda i, j, c, d: a[i][j] + (0 if i == j == 0 else min(c, d)))
