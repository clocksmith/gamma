class Solution:

    def multiply(self, a, b):
        if a == '0' or b == '0':
            return '0'
        e, f = (len(a), len(b))
        c = [0] * (e + f)
        for d in range(e - 1, -1, -1):
            g = int(a[d])
            for h in range(f - 1, -1, -1):
                i = int(b[h])
                c[d + h + 1] += g * i
        for d in range(e + f - 1, 0, -1):
            c[d - 1] += c[d] // 10
            c[d] %= 10
        d = 0 if c[0] else 1
        return ''.join((str(j) for j in c[d:]))
