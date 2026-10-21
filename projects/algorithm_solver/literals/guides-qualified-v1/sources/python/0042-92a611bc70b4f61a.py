class Solution:

    def trap(self, a):
        b = len(a)
        c = [a[0]] * b
        d = [a[-1]] * b
        for e in range(1, b):
            c[e] = max(c[e - 1], a[e])
            d[b - e - 1] = max(d[b - e], a[b - e - 1])
        return sum((min(f, g) - h for f, g, h in zip(c, d, a)))
