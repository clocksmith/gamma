"""2573. Find the String with LCP."""

def solve(lcp: list[list[int]]) -> str:
    """O(n^2) time, O(n) space; assign smallest letters, then verify the full recurrence."""
    size = len(lcp)
    letters = [-1] * size
    next_letter = 0
    for index in range(size):
        if letters[index] >= 0:
            continue
        if next_letter == 26:
            return ''
        letters[index] = next_letter
        for other in range(index + 1, size):
            if lcp[index][other] > 0:
                if letters[other] >= 0 and letters[other] != next_letter:
                    return ''
                letters[other] = next_letter
        next_letter += 1
    for first in range(size - 1, -1, -1):
        for second in range(size - 1, -1, -1):
            expected = 0
            if letters[first] == letters[second]:
                expected = 1
                if first + 1 < size and second + 1 < size:
                    expected += lcp[first + 1][second + 1]
            if lcp[first][second] != expected:
                return ''
    return ''.join(chr(97 + letter) for letter in letters)


class Solution:
    def findTheString(self, lcp: list[list[int]]) -> str:
        return solve(lcp)
