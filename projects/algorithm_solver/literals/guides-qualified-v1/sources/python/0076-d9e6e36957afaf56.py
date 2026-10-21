from collections import Counter
from math import inf
class Solution:

    def minWindow(self, a, b):
        c = Counter(b)
        d = Counter()
        e = f = 0
        g, h = (-1, inf)
        for i, j in enumerate(a):
            d[j] += 1
            if c[j] >= d[j]:
                e += 1
            while e == len(b):
                if i - f + 1 < h:
                    h = i - f + 1
                    g = f
                if c[a[f]] >= d[a[f]]:
                    e -= 1
                d[a[f]] -= 1
                f += 1
        return '' if g < 0 else a[g:g + h]
