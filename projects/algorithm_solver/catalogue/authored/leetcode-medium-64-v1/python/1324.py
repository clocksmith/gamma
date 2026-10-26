"""1324. Print Words Vertically: transpose word characters and remove only trailing padding."""


def solve(s: str) -> list[str]:
    """O(w * h) time and O(w * h) space for w words and maximum length h; inputs are read-only."""
    words = s.split(' ')
    height = max(map(len, words))
    answer = []
    for row in range(height):
        line = ''.join(word[row] if row < len(word) else ' ' for word in words)
        answer.append(line.rstrip(' '))
    return answer


class Solution:
    def printVertically(self, s: str) -> list[str]:
        return solve(s)
