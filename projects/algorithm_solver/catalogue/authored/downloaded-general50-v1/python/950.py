"""950. Reveal Cards In Increasing Order (Medium).

Specification: https://leetcode.com/problems/reveal-cards-in-increasing-order/description/
"""


def solve(deck: list[int]) -> list[int]:
    from collections import deque
    ordered = sorted(deck)
    result = [0] * len(deck)
    queue = deque(range(len(deck)))
    for card in ordered:
        idx = queue.popleft()
        result[idx] = card
        if queue:
            queue.append(queue.popleft())
    return result


class Solution:
    def deckRevealedIncreasing(self, deck: list[int]) -> list[int]:
        return solve(deck)
