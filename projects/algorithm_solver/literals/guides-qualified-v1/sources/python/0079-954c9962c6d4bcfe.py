from itertools import pairwise
class Solution:

    def exist(self, b, c):

        def a(d, e, f):
            if f == len(c) - 1:
                return b[d][e] == c[f]
            if b[d][e] != c[f]:
                return False
            g = b[d][e]
            b[d][e] = '0'
            for j, k in pairwise((-1, 0, 1, 0, -1)):
                m, n = (d + j, e + k)
                l = 0 <= m < h and 0 <= n < i and (b[m][n] != '0')
                if l and a(m, n, f + 1):
                    return True
            b[d][e] = g
            return False
        h, i = (len(b), len(b[0]))
        return any((a(d, e, 0) for d in range(h) for e in range(i)))
