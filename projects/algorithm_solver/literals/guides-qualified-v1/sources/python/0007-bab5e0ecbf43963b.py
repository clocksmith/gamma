class Solution:

    def reverse(self, a):
        b = 0
        c, d = (-2 ** 31, 2 ** 31 - 1)
        while a:
            if b < c // 10 + 1 or b > d // 10:
                return 0
            e = a % 10
            if a < 0 and e > 0:
                e -= 10
            b = b * 10 + e
            a = (a - e) // 10
        return b
