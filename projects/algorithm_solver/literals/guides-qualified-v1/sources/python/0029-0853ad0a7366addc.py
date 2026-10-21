class Solution:

    def divide(self, a, b):
        c = -2 ** 31
        d = 2 ** 31 - 1
        if a == 0:
            return 0
        e = -1
        if (a < 0) == (b < 0):
            e = 1
        f = abs(a)
        g = abs(b)
        if g > f:
            return 0
        h = 0
        while f >= g:
            j = g
            k = 0
            while j << 1 <= f:
                j <<= 1
                k += 1
            h += 1 << k
            f -= j
        i = e * h
        if i < c:
            return c
        elif i > d:
            return d
        else:
            return i
