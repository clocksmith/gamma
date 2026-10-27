"""4008. Minimum Initial Strength to Defeat All Monsters.

Specification: https://leetcode.com/problems/minimum-initial-strength-to-defeat-all-monsters/description/
"""

from __future__ import annotations


def solve(monsters: list[int], boosts: list[list[int]]) -> int:
    """O(n+q) time and O(n) space; bonuses enable a fight but never replenish strength. Inputs are preserved."""
    difference = [0] * (len(monsters) + 1)
    for left, right, value in boosts:
        difference[left] += value
        difference[right + 1] -= value
    bonus = consumed = answer = 0
    for index, strength in enumerate(monsters):
        bonus += difference[index]
        needed = strength - bonus
        if needed > 0:
            answer = max(answer, consumed + needed)
        consumed += strength
    return answer
