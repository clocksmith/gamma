"""2140. Solving Questions With Brainpower: choose between skipping a question and jumping past its forced break."""


def solve(questions: list[list[int]]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    size = len(questions)
    best = [0] * (size + 1)
    for index in range(size - 1, -1, -1):
        points, skip = questions[index]
        following = min(size, index + skip + 1)
        best[index] = max(best[index + 1], points + best[following])
    return best[0]


class Solution:
    def mostPoints(self, questions: list[list[int]]) -> int:
        return solve(questions)
