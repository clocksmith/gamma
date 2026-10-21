class Solution:

    def firstMissingPositive(self, a):
        b = len(a)
        for c in range(b):
            while 1 <= a[c] <= b and a[c] != a[a[c] - 1]:
                d = a[c] - 1
                a[c], a[d] = (a[d], a[c])
        for c in range(b):
            if a[c] != c + 1:
                return c + 1
        return b + 1
