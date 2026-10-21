class Solution:

    def combine(self, b, c):

        def a(f):
            if len(e) == c:
                d.append(e[:])
                return
            if f > b:
                return
            e.append(f)
            a(f + 1)
            e.pop()
            a(f + 1)
        d = []
        e = []
        a(1)
        return d
