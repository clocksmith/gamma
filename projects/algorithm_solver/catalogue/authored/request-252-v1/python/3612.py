def solve(s):
    result = []
    for char in s:
        if char == '*':
            if result:
                result.pop()
        elif char == '#':
            result *= 2
        elif char == '%':
            result.reverse()
        else:
            result.append(char)
    return ''.join(result)
