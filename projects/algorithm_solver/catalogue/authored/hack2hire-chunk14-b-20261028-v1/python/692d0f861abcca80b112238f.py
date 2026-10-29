"""Hack2Hire 692d0f861abcca80b112238f (Basic Calculator) over an INFERRED spec; qualification unknown."""


def divide(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def solve(s):
    stack = []
    total, term, sign, mulop, negate = 0, 0, 1, '', False
    expect_operand = True
    i, n = 0, len(s)

    def combine(term, mulop, value):
        if mulop == '*':
            return term * value
        if mulop == '/':
            return divide(term, value)
        return value

    while i < n:
        ch = s[i]
        if '0' <= ch <= '9':
            j = i
            while j < n and '0' <= s[j] <= '9':
                j += 1
            value = int(s[i:j])
            if negate:
                value = -value
            term = combine(term, mulop, value)
            mulop, negate, expect_operand = '', False, False
            i = j
            continue
        if expect_operand:
            if ch == '-':
                negate = not negate
            else:  # '('
                stack.append((total, term, sign, mulop, negate))
                total, term, sign, mulop, negate = 0, 0, 1, '', False
        elif ch == ')':
            value = total + sign * term
            total, term, sign, mulop, negate = stack.pop()
            if negate:
                value = -value
            term = combine(term, mulop, value)
            mulop, negate = '', False
        elif ch == '+' or ch == '-':
            total += sign * term
            term, sign, expect_operand = 0, (1 if ch == '+' else -1), True
        else:
            mulop, expect_operand = ch, True
        i += 1
    return total + sign * term


class Solution:
    def calculate(self, s):
        return solve(s)
