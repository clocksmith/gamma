class Solution:

    def combinationSum2(self, b, c):

        def a(f, g):
            if g == 0:
                d.append(e[:])
                return
            if f >= len(b) or g < b[f]:
                return
            for h in range(f, len(b)):
                if h > f and b[h] == b[h - 1]:
                    continue
                e.append(b[h])
                a(h + 1, g - b[h])
                e.pop()
        b.sort()
        d = []
        e = []
        a(0, c)
        return d
