"""2232. Minimize Result by Adding Parentheses to Expression: enumerate legal parenthesis boundaries and evaluate the resulting factors."""


def solve(expression: str) -> str:
    """O(L^3) time and O(L) auxiliary space for expression length L; inputs are read-only."""
    left, right = expression.split('+')
    best = float('inf')
    answer = ''
    for start in range(len(left)):
        outer_left = int(left[:start]) if start else 1
        inner_left = int(left[start:])
        for end in range(1, len(right) + 1):
            inner_right = int(right[:end])
            outer_right = int(right[end:]) if end < len(right) else 1
            value = outer_left * (inner_left + inner_right) * outer_right
            if value < best:
                best = value
                answer = left[:start] + '(' + left[start:] + '+' + right[:end] + ')' + right[end:]
    return answer


class Solution:
    def minimizeResult(self, expression: str) -> str:
        return solve(expression)
