class Solution:

    def climbStairs(self, a):
        c, d = (0, 1)
        for b in range(a):
            c, d = (d, c + d)
        return d
