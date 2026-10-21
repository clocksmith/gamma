class Solution:

    def maxArea(self, a):
        c, d = (0, len(a) - 1)
        b = 0
        while c < d:
            e = min(a[c], a[d]) * (d - c)
            b = max(b, e)
            if a[c] < a[d]:
                c += 1
            else:
                d -= 1
        return b
