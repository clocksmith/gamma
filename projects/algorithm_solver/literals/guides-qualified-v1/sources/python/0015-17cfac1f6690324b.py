class Solution:

    def threeSum(self, a):
        a.sort()
        b = len(a)
        c = []
        for d in range(b - 2):
            if a[d] > 0:
                break
            if d and a[d] == a[d - 1]:
                continue
            e, f = (d + 1, b - 1)
            while e < f:
                g = a[d] + a[e] + a[f]
                if g < 0:
                    e += 1
                elif g > 0:
                    f -= 1
                else:
                    c.append([a[d], a[e], a[f]])
                    e, f = (e + 1, f - 1)
                    while e < f and a[e] == a[e - 1]:
                        e += 1
                    while e < f and a[f] == a[f + 1]:
                        f -= 1
        return c
