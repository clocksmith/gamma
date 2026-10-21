class Solution:

    def mySqrt(self, a):
        b, c = (0, a)
        while b < c:
            d = b + c + 1 >> 1
            if d > a // d:
                c = d - 1
            else:
                b = d
        return b
