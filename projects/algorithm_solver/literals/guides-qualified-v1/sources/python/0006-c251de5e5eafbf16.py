from itertools import chain
class Solution:

    def convert(self, a, b):
        if b == 1:
            return a
        c = [[] for g in range(b)]
        e, f = (0, -1)
        for d in a:
            c[e].append(d)
            if e == 0 or e == b - 1:
                f = -f
            e += f
        return ''.join(chain(*c))
