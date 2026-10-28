class Solution:
    def isNumber(self, s):
        i, n = 0, len(s)
        if i < n and s[i] in '+-':
            i += 1
        digits = 0
        while i < n and '0' <= s[i] <= '9':
            digits += 1
            i += 1
        if i < n and s[i] == '.':
            i += 1
            while i < n and '0' <= s[i] <= '9':
                digits += 1
                i += 1
        if digits == 0:
            return False
        if i < n and s[i] in 'eE':
            i += 1
            if i < n and s[i] in '+-':
                i += 1
            start = i
            while i < n and '0' <= s[i] <= '9':
                i += 1
            if i == start:
                return False
        return i == n
