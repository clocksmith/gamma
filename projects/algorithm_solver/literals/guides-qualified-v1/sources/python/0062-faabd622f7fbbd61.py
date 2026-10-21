def f(a, b, c, d):
    e = [c] * b
    for i in range(a):
        g = c
        for j in range(b):
            e[j] = g = d(i, j, e[j], g)
    return e[-1]
class Solution:

    def uniquePaths(self, a, b):
        return f(a, b, 0, lambda i, j, c, d: 1 if i == j == 0 else c + d)
