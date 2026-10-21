class Solution:

    def countAndSay(self, a):
        b = '1'
        for c in range(a - 1):
            d = 0
            e = []
            while d < len(b):
                f = d
                while f < len(b) and b[f] == b[d]:
                    f += 1
                e.append(str(f - d))
                e.append(str(b[d]))
                d = f
            b = ''.join(e)
        return b
