class Solution:

    def totalNQueens(self, b):

        def a(g):
            if g == b:
                nonlocal f
                f += 1
                return
            for h in range(b):
                i, j = (g + h, g - h + b)
                if c[h] or d[i] or e[j]:
                    continue
                c[h] = d[i] = e[j] = True
                a(g + 1)
                c[h] = d[i] = e[j] = False
        c = [False] * 10
        d = [False] * 20
        e = [False] * 20
        f = 0
        a(0)
        return f
