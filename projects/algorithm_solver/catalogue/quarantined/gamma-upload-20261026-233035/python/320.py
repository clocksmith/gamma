"""320. Generalized Abbreviation."""
def solve(word: str) -> list[str]:
    result = []
    def visit(index: int, count: int, path: list[str]) -> None:
        if index == len(word):
            if count:
                path.append(str(count))
            result.append(''.join(path))
            if count:
                path.pop()
            return
        visit(index + 1, count + 1, path)
        if count:
            path.append(str(count))
        path.append(word[index])
        visit(index + 1, 0, path)
        path.pop()
        if count:
            path.pop()
    visit(0, 0, [])
    return result

class Solution:
    def generateAbbreviations(self, word: str) -> list[str]:
        return solve(word)
