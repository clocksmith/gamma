class Solution:

    def plusOne(self, a):
        b = len(a)
        for c in range(b - 1, -1, -1):
            a[c] += 1
            a[c] %= 10
            if a[c] != 0:
                return a
        return [1] + a
