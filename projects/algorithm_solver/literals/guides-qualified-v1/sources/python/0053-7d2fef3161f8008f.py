class Solution:

    def maxSubArray(self, a):
        b = c = a[0]
        for d in a[1:]:
            c = max(c, 0) + d
            b = max(b, c)
        return b
