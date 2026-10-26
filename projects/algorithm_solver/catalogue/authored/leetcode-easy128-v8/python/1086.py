"""1086. High Five (Easy).

Specification: https://leetcode.com/problems/high-five/description/
"""


def solve(items: list[list[int]]) -> list[list[int]]:
    """O(n + u log u) time, O(u) space; retain five highest scores per ID and floor averages."""
    scores = {}
    for student, score in items:
        best = scores.setdefault(student, [])
        best.append(score)
        best.sort(reverse=True)
        if len(best) > 5:
            best.pop()
    return [[student, sum(scores[student]) // 5] for student in sorted(scores)]


class Solution:
    def highFive(self, items: list[list[int]]) -> list[list[int]]:
        return solve(items)
