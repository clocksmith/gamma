from functools import cache
class Solution:

    def isMatch(self, b, c):

        @cache
        def a(d, e):
            if e >= g:
                return d == f
            if e + 1 < g and c[e + 1] == '*':
                return a(d, e + 2) or (d < f and (b[d] == c[e] or c[e] == '.') and a(d + 1, e))
            return d < f and (b[d] == c[e] or c[e] == '.') and a(d + 1, e + 1)
        f, g = (len(b), len(c))
        return a(0, 0)
