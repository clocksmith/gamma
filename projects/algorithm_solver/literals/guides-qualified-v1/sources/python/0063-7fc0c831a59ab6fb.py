def f(a, b, c, d):
    e = [c] * b
    for i in range(a):
        g = c
        for j in range(b):
            e[j] = g = d(i, j, e[j], g)
    return e[-1]
class Solution:

    def uniquePathsWithObstacles(self, a):
        return f(len(a), len(a[0]), 0, lambda i, j, c, d: 0 if a[i][j] else 1 if i == j == 0 else c + d)
