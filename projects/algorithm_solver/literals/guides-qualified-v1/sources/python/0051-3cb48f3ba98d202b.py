class Solution:

    def solveNQueens(self, b):

        def a(h):
            if h == b:
                c.append([''.join(k) for k in d])
                return
            for i in range(b):
                if e[i] + f[h + i] + g[b - h + i] == 0:
                    d[h][i] = 'Q'
                    e[i] = f[h + i] = g[b - h + i] = 1
                    a(h + 1)
                    e[i] = f[h + i] = g[b - h + i] = 0
                    d[h][i] = '.'
        c = []
        d = [['.'] * b for j in range(b)]
        e = [0] * b
        f = [0] * (b << 1)
        g = [0] * (b << 1)
        a(0)
        return c
