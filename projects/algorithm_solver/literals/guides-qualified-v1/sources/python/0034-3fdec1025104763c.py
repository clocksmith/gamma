from bisect import bisect_left
class Solution:

    def searchRange(self, a, b):
        c = bisect_left(a, b)
        d = bisect_left(a, b + 1)
        return [-1, -1] if c == d else [c, d - 1]
