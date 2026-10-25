class Solution:
    def baseNeg2(self, n):
        if n == 0:
            return "0"
        digits = []
        value = n
        while value != 0:
            remainder = value % 2
            digits.append(str(remainder))
            value = (value - remainder) // -2
        return "".join(reversed(digits))
