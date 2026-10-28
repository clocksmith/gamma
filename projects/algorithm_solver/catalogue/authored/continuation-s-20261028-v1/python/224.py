class Solution:
    def calculate(self, s):
        contexts = [1]
        sign = 1
        result = 0
        i = 0
        while i < len(s):
            c = s[i]
            if '0' <= c <= '9':
                value = 0
                while i < len(s) and '0' <= s[i] <= '9':
                    value = value * 10 + ord(s[i]) - 48
                    i += 1
                result += sign * value
                continue
            if c == '+':
                sign = contexts[-1]
            elif c == '-':
                sign = -contexts[-1]
            elif c == '(':
                contexts.append(sign)
            elif c == ')':
                contexts.pop()
            i += 1
        return result
