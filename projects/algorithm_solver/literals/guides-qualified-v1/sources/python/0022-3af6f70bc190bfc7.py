class Solution:

    def generateParenthesis(self, b):

        def a(d, e, f):
            if d > b or e > b or d < e:
                return
            if d == b and e == b:
                c.append(f)
                return
            a(d + 1, e, f + '(')
            a(d, e + 1, f + ')')
        c = []
        a(0, 0, '')
        return c
