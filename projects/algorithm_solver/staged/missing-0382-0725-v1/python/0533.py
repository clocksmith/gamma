"""533. Lonely Pixel II."""

from collections import Counter

def solve(picture: list[list[str]], target: int) -> int:
    rows = Counter(''.join(row) for row in picture)
    columns = [sum(row[c] == 'B' for row in picture) for c in range(len(picture[0]))]
    answer = 0
    for row, copies in rows.items():
        if copies == target and row.count('B') == target:
            answer += target * sum(char == 'B' and columns[c] == target for c, char in enumerate(row))
    return answer


class Solution:
    def findBlackPixel(self, picture: list[list[str]], target: int) -> int:
        return solve(picture, target)
