from math import inf
class Solution:

    def findMedianSortedArrays(self, b, c):

        def a(f, g, h):
            if f >= l:
                return c[g + h - 1]
            if g >= m:
                return b[f + h - 1]
            if h == 1:
                return min(b[f], c[g])
            i = h // 2
            j = b[f + i - 1] if f + i - 1 < l else inf
            k = c[g + i - 1] if g + i - 1 < m else inf
            return a(f + i, g, h - i) if j < k else a(f, g + i, h - i)
        l, m = (len(b), len(c))
        d = a(0, 0, (l + m + 1) // 2)
        e = a(0, 0, (l + m + 2) // 2)
        return (d + e) / 2
