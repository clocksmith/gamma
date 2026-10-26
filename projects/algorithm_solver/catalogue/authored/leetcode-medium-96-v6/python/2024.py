"""2024. Maximize the Confusion of an Exam: maintain a window whose minority answer count can be changed."""


def solve(answerKey: str, k: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    left = true_count = best = 0
    for right, answer in enumerate(answerKey):
        true_count += answer == 'T'
        while min(true_count, right - left + 1 - true_count) > k:
            true_count -= answerKey[left] == 'T'
            left += 1
        best = max(best, right - left + 1)
    return best


class Solution:
    def maxConsecutiveAnswers(self, answerKey: str, k: int) -> int:
        return solve(answerKey, k)
