class Solution:

    def fourSum(self, a, b):
        c = len(a)
        d = []
        if c < 4:
            return d
        a.sort()
        for e in range(c - 3):
            if e and a[e] == a[e - 1]:
                continue
            for f in range(e + 1, c - 2):
                if f > e + 1 and a[f] == a[f - 1]:
                    continue
                g, h = (f + 1, c - 1)
                while g < h:
                    i = a[e] + a[f] + a[g] + a[h]
                    if i < b:
                        g += 1
                    elif i > b:
                        h -= 1
                    else:
                        d.append([a[e], a[f], a[g], a[h]])
                        g, h = (g + 1, h - 1)
                        while g < h and a[g] == a[g - 1]:
                            g += 1
                        while g < h and a[h] == a[h + 1]:
                            h -= 1
        return d
