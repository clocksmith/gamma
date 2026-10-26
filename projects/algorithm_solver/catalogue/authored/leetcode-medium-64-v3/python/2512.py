"""2512. Reward Top K Students: score feedback words and break score ties by student identifier."""


def solve(positive_feedback: list[str], negative_feedback: list[str], report: list[str], student_id: list[int], k: int) -> list[int]:
    """O(S + n log n) expected time and O(S + n) auxiliary space for total text S; inputs are read-only."""
    positive = set(positive_feedback)
    negative = set(negative_feedback)
    ranked = []
    for text, student in zip(report, student_id):
        score = 0
        for word in text.split():
            if word in positive:
                score += 3
            elif word in negative:
                score -= 1
        ranked.append((-score, student))
    ranked.sort()
    return [student for _, student in ranked[:k]]


class Solution:
    def topStudents(self, positive_feedback: list[str], negative_feedback: list[str], report: list[str], student_id: list[int], k: int) -> list[int]:
        return solve(positive_feedback, negative_feedback, report, student_id, k)
