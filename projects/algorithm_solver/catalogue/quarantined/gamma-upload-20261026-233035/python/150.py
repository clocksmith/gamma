"""150. Evaluate Reverse Polish Notation."""
def solve(tokens: list[str]) -> int:
    stack = []
    for token in tokens:
        if token in '+-*/':
            right, left = stack.pop(), stack.pop()
            if token == '+':
                stack.append(left + right)
            elif token == '-':
                stack.append(left - right)
            elif token == '*':
                stack.append(left * right)
            else:
                stack.append(int(left / right))
        else:
            stack.append(int(token))
    return stack[-1]

class Solution:
    def evalRPN(self, tokens: list[str]) -> int:
        return solve(tokens)
