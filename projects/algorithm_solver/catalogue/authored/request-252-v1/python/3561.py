def solve(s):
    stack = []
    for char in s:
        if stack and abs(ord(char) - ord(stack[-1])) in (1, 25):
            stack.pop()
        else:
            stack.append(char)
    return ''.join(stack)
