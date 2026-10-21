class Solution:

    def insert(self, b, c):

        def a(b):
            b.sort()
            d = [b[0]]
            for e, f in b[1:]:
                if d[-1][1] < e:
                    d.append([e, f])
                else:
                    d[-1][1] = max(d[-1][1], f)
            return d
        b.append(c)
        return a(b)
