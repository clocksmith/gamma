"""439. Ternary Expression Parser. Reduce right-associated ternary expressions from right to left."""

def solve(expression: str) -> str:
    stack = []
    for char in reversed(expression):
        if stack and stack[-1] == '?':
            stack.pop()
            yes = stack.pop()
            stack.pop()
            no = stack.pop()
            stack.append(yes if char == 'T' else no)
        else:
            stack.append(char)
    return stack[-1]


class Solution:
    def parseTernary(self, expression: str) -> str:
        return solve(expression)
