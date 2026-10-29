"""Hack2Hire 677b092f78175fce2ecdfc0e (Simplify Expression) over an INFERRED spec; qualification unknown."""


def solve(expression):
    terms = []
    groups = [1]
    pending = 1
    i = 0
    n = len(expression)
    while i < n:
        c = expression[i]
        if c == '+':
            pending = 1
            i += 1
        elif c == '-':
            pending = -1
            i += 1
        elif c == '(':
            groups.append(groups[-1] * pending)
            pending = 1
            i += 1
        elif c == ')':
            groups.pop()
            i += 1
        else:
            j = i
            while j < n and 'a' <= expression[j] <= 'z':
                j += 1
            terms.append(('-' if groups[-1] * pending < 0 else '+') + expression[i:j])
            pending = 1
            i = j
    text = ''.join(terms)
    return text[1:] if text[0] == '+' else text


class Solution:
    def simplifyExpression(self, expression):
        return solve(expression)
