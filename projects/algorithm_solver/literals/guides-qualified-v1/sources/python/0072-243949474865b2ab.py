class Solution:

    def minDistance(self, a, b):
        e, f = (len(a), len(b))
        c = [[0] * (f + 1) for i in range(e + 1)]
        for d in range(1, f + 1):
            c[0][d] = d
        for g, h in enumerate(a, 1):
            c[g][0] = g
            for d, j in enumerate(b, 1):
                if h == j:
                    c[g][d] = c[g - 1][d - 1]
                else:
                    c[g][d] = min(c[g - 1][d], c[g][d - 1], c[g - 1][d - 1]) + 1
        return c[e][f]
