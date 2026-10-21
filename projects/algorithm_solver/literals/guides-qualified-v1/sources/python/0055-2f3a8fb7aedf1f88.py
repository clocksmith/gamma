class Solution:

    def canJump(self, a):
        b = 0
        for c, d in enumerate(a):
            if b < c:
                return False
            b = max(b, c + d)
        return True
