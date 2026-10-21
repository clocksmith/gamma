class Solution:

    def intToRoman(self, a):
        b = ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
        c = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
        d = []
        for e, f in zip(b, c):
            while a >= f:
                a -= f
                d.append(e)
        return ''.join(d)
