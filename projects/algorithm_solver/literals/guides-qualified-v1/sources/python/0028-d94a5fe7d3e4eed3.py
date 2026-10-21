class Solution:

    def strStr(self, a, b):
        d, e = (len(a), len(b))
        for c in range(d - e + 1):
            if a[c:c + e] == b:
                return c
        return -1
