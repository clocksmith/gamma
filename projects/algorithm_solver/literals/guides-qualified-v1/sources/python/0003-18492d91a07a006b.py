class Solution:

    def lengthOfLongestSubstring(self, a):
        b = set()
        c = d = 0
        for e, f in enumerate(a):
            while f in b:
                b.remove(a[d])
                d += 1
            b.add(f)
            c = max(c, e - d + 1)
        return c
