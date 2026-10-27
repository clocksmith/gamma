"""32. Longest Valid Parentheses."""
def solve(s: str) -> int:
    stack = [-1]
    best = 0
    for index, char in enumerate(s):
        if char == '(':
            stack.append(index)
        else:
            stack.pop()
            if stack:
                best = max(best, index - stack[-1])
            else:
                stack.append(index)
    return best

class Solution:
    def longestValidParentheses(self, s: str) -> int:
        return solve(s)
