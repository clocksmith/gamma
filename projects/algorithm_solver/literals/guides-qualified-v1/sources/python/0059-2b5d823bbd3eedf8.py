class Solution:

    def generateMatrix(self, a):
        b = [[0] * a for h in range(a)]
        c = (0, 1, 0, -1, 0)
        d = e = f = 0
        for g in range(1, a * a + 1):
            b[d][e] = g
            i, j = (d + c[f], e + c[f + 1])
            if i < 0 or i >= a or j < 0 or (j >= a) or b[i][j]:
                f = (f + 1) % 4
            d, e = (d + c[f], e + c[f + 1])
        return b
