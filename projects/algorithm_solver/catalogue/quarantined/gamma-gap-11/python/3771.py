"""3771. Total Score of Dungeon Runs."""
from __future__ import annotations
from bisect import bisect_left


def solve(hp: int, damage: list[int], requirement: list[int]) -> int:
    """O(n log n) time and O(n) space; count eligible starting rooms for each earned point."""
    prefix = [0]
    for value in damage:
        prefix.append(prefix[-1] + value)
    answer = 0
    for index, needed in enumerate(requirement):
        threshold = prefix[index + 1] + needed - hp
        first = bisect_left(prefix, threshold, 0, index + 1)
        answer += index + 1 - first
    return answer


class Solution:
    def totalScore(self, hp: int, damage: list[int], requirement: list[int]) -> int:
        return solve(hp, damage, requirement)
