class Solution:

    def longestCommonPrefix(self, a):
        for b in range(len(a[0])):
            for c in a[1:]:
                if len(c) <= b or c[b] != a[0][b]:
                    return c[:b]
        return a[0]
