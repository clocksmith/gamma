from functools import cache
class Solution:

    def isMatch(self, b, c):

        @cache
        def a(d, e):
            if d >= len(b):
                return e >= len(c) or (c[e] == '*' and a(d, e + 1))
            if e >= len(c):
                return False
            if c[e] == '*':
                return a(d + 1, e) or a(d + 1, e + 1) or a(d, e + 1)
            return (c[e] == '?' or b[d] == c[e]) and a(d + 1, e + 1)
        return a(0, 0)
