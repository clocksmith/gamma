"""131. Palindrome Partitioning."""
def solve(s: str) -> list[list[str]]:
    result = []
    path = []
    def visit(start: int) -> None:
        if start == len(s):
            result.append(path.copy())
            return
        for end in range(start + 1, len(s) + 1):
            piece = s[start:end]
            if piece == piece[::-1]:
                path.append(piece)
                visit(end)
                path.pop()
    visit(0)
    return result

class Solution:
    def partition(self, s: str) -> list[list[str]]:
        return solve(s)
