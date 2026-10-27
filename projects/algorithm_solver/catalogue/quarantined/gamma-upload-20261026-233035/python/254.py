"""254. Factor Combinations."""
def solve(n: int) -> list[list[int]]:
    result = []
    path = []
    def visit(start: int, remaining: int) -> None:
        factor = start
        while factor * factor <= remaining:
            if remaining % factor == 0:
                path.append(factor)
                result.append(path + [remaining // factor])
                visit(factor, remaining // factor)
                path.pop()
            factor += 1
    visit(2, n)
    return result

class Solution:
    def getFactors(self, n: int) -> list[list[int]]:
        return solve(n)
