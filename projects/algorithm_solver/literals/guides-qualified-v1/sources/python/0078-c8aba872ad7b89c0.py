class Solution:

    def subsets(self, b):

        def a(e):
            if e == len(b):
                c.append(d[:])
                return
            a(e + 1)
            d.append(b[e])
            a(e + 1)
            d.pop()
        c = []
        d = []
        a(0)
        return c
