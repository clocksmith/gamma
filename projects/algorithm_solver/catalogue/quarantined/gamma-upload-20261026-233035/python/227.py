"""227. Basic Calculator II."""
def solve(s: str) -> int:
    stack = []
    number = 0
    operation = '+'
    for char in s + '+':
        if char.isdigit():
            number = number * 10 + int(char)
        elif char != ' ':
            if operation == '+':
                stack.append(number)
            elif operation == '-':
                stack.append(-number)
            elif operation == '*':
                stack[-1] *= number
            else:
                stack[-1] = int(stack[-1] / number)
            operation = char
            number = 0
    return sum(stack)

class Solution:
    def calculate(self, s: str) -> int:
        return solve(s)
