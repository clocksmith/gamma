class Solution:
    def bitwiseComplement(self, n):
        if n == 0:
            return 1
        boundary = 1
        while boundary <= n:
            boundary *= 2
        return boundary - 1 - n
