class Solution:

    def lengthOfLastWord(self, a):
        b = len(a) - 1
        while b >= 0 and a[b] == ' ':
            b -= 1
        c = b
        while c >= 0 and a[c] != ' ':
            c -= 1
        return b - c
