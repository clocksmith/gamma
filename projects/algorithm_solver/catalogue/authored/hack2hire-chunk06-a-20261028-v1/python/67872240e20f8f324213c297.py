"""Hack2Hire 67872240e20f8f324213c297 (Evaluate String Expression) over an INFERRED spec; qualification unknown."""


def solve(expression):
    s, n = expression, len(expression)
    stack = []  # frames [is_add, accumulated value, argument count]
    result = None
    i = 0
    while i < n:
        ch = s[i]
        if ch == ' ' or ch == '(' or ch == ',':
            i += 1
        elif ch == 'a' or ch == 's':
            stack.append([ch == 'a', 0, 0])
            i += 3
        elif ch == ')':
            value = stack.pop()[1]
            i += 1
            if stack:
                frame = stack[-1]
                frame[1] = frame[1] + value if frame[0] or frame[2] == 0 else frame[1] - value
                frame[2] += 1
            else:
                result = value
        else:
            j = i + 1 if ch == '-' else i
            while j < n and '0' <= s[j] <= '9':
                j += 1
            value = int(s[i:j])
            i = j
            if stack:
                frame = stack[-1]
                frame[1] = frame[1] + value if frame[0] or frame[2] == 0 else frame[1] - value
                frame[2] += 1
            else:
                result = value
    return result


class Solution:
    def evaluate(self, expression):
        return solve(expression)
