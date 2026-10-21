class Solution:

    def myAtoi(self, a):
        if not a:
            return 0
        b = len(a)
        if b == 0:
            return 0
        c = 0
        while a[c] == ' ':
            c += 1
            if c == b:
                return 0
        d = -1 if a[c] == '-' else 1
        if a[c] in ['-', '+']:
            c += 1
        e, f = (0, (2 ** 31 - 1) // 10)
        while c < b:
            if not a[c].isdigit():
                break
            g = int(a[c])
            if e > f or (e == f and g > 7):
                return 2 ** 31 - 1 if d > 0 else -2 ** 31
            e = e * 10 + g
            c += 1
        return d * e
