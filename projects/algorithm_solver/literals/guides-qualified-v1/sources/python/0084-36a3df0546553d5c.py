class Solution:

    def largestRectangleArea(self, a):
        b = len(a)
        c = []
        d = [-1] * b
        e = [b] * b
        for f, g in enumerate(a):
            while c and a[c[-1]] >= g:
                e[c[-1]] = f
                c.pop()
            if c:
                d[f] = c[-1]
            c.append(f)
        return max((g * (e[f] - d[f] - 1) for f, g in enumerate(a)))
