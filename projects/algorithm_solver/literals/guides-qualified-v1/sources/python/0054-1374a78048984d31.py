class Solution:

    def spiralOrder(self, a):
        i, j = (len(a), len(a[0]))
        b = (0, 1, 0, -1, 0)
        c = [[False] * j for h in range(i)]
        d = e = f = 0
        g = []
        for h in range(i * j):
            g.append(a[d][e])
            c[d][e] = True
            k, l = (d + b[f], e + b[f + 1])
            if k < 0 or k >= i or l < 0 or (l >= j) or c[k][l]:
                f = (f + 1) % 4
            d += b[f]
            e += b[f + 1]
        return g
