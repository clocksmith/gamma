"""Hack2Hire 678d3e738c349080cddc5f5e (Evaluate String Expression II) over an INFERRED spec; qualification unknown."""


def solve(expression):
    stack = []  # frames [operation, accumulator]
    result = None
    i = 0
    n = len(expression)
    while i < n:
        c = expression[i]
        if c == ' ':
            i += 1
            continue
        if c == '(':
            i += 1
            while expression[i] == ' ':
                i += 1
            operation = expression[i:i + 3]
            i += 3
            stack.append([operation, 0 if operation == 'add' else 1])
            continue
        if c == ')':
            value = stack.pop()[1]
            i += 1
        else:
            j = i + 1
            while j < n and expression[j] not in ' ()':
                j += 1
            value = int(expression[i:j])
            i = j
        if stack:
            frame = stack[-1]
            frame[1] = frame[1] + value if frame[0] == 'add' else frame[1] * value
        else:
            result = value
    return result


class Solution:
    def evaluate(self, expression):
        return solve(expression)
