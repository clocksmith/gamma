from math import inf
class Solution:

    def threeSumClosest(self, a, b):
        a.sort()
        c = len(a)
        d = inf
        for e, f in enumerate(a):
            g, h = (e + 1, c - 1)
            while g < h:
                i = f + a[g] + a[h]
                if i == b:
                    return i
                if abs(i - b) < abs(d - b):
                    d = i
                if i > b:
                    h -= 1
                else:
                    g += 1
        return d
