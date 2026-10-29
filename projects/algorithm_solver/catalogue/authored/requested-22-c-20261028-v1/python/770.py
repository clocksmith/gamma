"""Original frontend 770 variant; qualification not qualified."""

def solve(expression, evalvars, evalints):
    env = dict(zip(evalvars, evalints))
    tokens = []
    i = 0
    while i < len(expression):
        ch = expression[i]
        if ch == ' ':
            i += 1
        elif ch.isalnum():
            j = i
            while j < len(expression) and expression[j].isalnum():
                j += 1
            tokens.append(expression[i:j])
            i = j
        else:
            tokens.append(ch)
            i += 1
    position = 0

    def combine(left, right, sign):
        result = dict(left)
        for key, value in right.items():
            result[key] = result.get(key, 0) + sign * value
        return {key: value for key, value in result.items() if value}

    def multiply(left, right):
        result = {}
        for a, x in left.items():
            for b, y in right.items():
                key = tuple(sorted(a + b))
                result[key] = result.get(key, 0) + x * y
        return {key: value for key, value in result.items() if value}

    def factor():
        nonlocal position
        token = tokens[position]
        position += 1
        if token == '(':
            value = expr()
            position += 1
            return value
        if token.isdigit():
            number = int(token)
            return {(): number} if number else {}
        if token in env:
            return {(): env[token]} if env[token] else {}
        return {(token,): 1}

    def term():
        nonlocal position
        value = factor()
        while position < len(tokens) and tokens[position] == '*':
            position += 1
            value = multiply(value, factor())
        return value

    def expr():
        nonlocal position
        value = term()
        while position < len(tokens) and tokens[position] in '+-':
            sign = 1 if tokens[position] == '+' else -1
            position += 1
            value = combine(value, term(), sign)
        return value

    polynomial = expr()
    ordered = sorted(polynomial.items(), key=lambda item: (-len(item[0]), item[0]))
    return [str(value) + ''.join('*' + name for name in key) for key, value in ordered]


class Solution:
    def basicCalculatorIV(self, expression, evalvars, evalints):
        return solve(expression, evalvars, evalints)
