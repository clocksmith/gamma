"""216. Combination Sum III."""
def solve(k: int, n: int) -> list[list[int]]:
    result = []
    path = []
    def visit(start: int, remaining: int) -> None:
        if len(path) == k:
            if remaining == 0:
                result.append(path.copy())
            return
        for value in range(start, 10):
            if value > remaining:
                break
            path.append(value)
            visit(value + 1, remaining - value)
            path.pop()
    visit(1, n)
    return result

class Solution:
    def combinationSum3(self, k: int, n: int) -> list[list[int]]:
        return solve(k, n)
