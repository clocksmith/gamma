class Solution:

    def searchInsert(self, a, b):
        c, d = (0, len(a))
        while c < d:
            e = c + d >> 1
            if a[e] >= b:
                d = e
            else:
                c = e + 1
        return c
