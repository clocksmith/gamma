"""3664. Two-Letter Card Game."""
from __future__ import annotations


def solve(cards: list[str], x: str) -> int:
    """O(n) time and O(1) auxiliary space for the fixed alphabet; inputs are preserved."""
    left = [0] * 26
    right = [0] * 26
    double = 0
    for card in cards:
        if card[0] == x and card[1] == x:
            double += 1
        elif card[0] == x:
            left[ord(card[1]) - 97] += 1
        elif card[1] == x:
            right[ord(card[0]) - 97] += 1
    left_total, right_total = sum(left), sum(right)
    left_max, right_max = max(left), max(right)
    answer = 0
    for assigned in range(double + 1):
        a = left_total + assigned
        b = right_total + double - assigned
        first = min(a // 2, a - max(left_max, assigned))
        second = min(b // 2, b - max(right_max, double - assigned))
        answer = max(answer, first + second)
    return answer


class Solution:
    def score(self, cards: list[str], x: str) -> int:
        return solve(cards, x)
