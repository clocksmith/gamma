class Solution:

    def isPalindrome(self, a):
        if a < 0 or (a and a % 10 == 0):
            return False
        b = 0
        while b < a:
            b = b * 10 + a % 10
            a //= 10
        return a in (b, b // 10)
