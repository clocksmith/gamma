class Solution:

    def merge(self, a):
        a.sort()
        b = []
        c, d = a[0]
        for e, f in a[1:]:
            if d < e:
                b.append([c, d])
                c, d = (e, f)
            else:
                d = max(d, f)
        b.append([c, d])
        return b
