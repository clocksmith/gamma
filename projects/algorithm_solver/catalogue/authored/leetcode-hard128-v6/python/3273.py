"""3273. Minimum Amount of Damage Dealt to Bob.

Order enemies by processing-time/damage ratio using integer cross-products; O(n log n) time and O(n) space. Inputs are preserved. The paired JavaScript result uses BigInt when Number is not exact.
"""

from functools import cmp_to_key


def solve(power: int, damage: list[int], health: list[int]) -> int:
    jobs = [((value + power - 1) // power, damage[index], index) for index, value in enumerate(health)]

    def compare(first, second):
        difference = first[0] * second[1] - second[0] * first[1]
        return difference if difference else first[2] - second[2]

    jobs.sort(key=cmp_to_key(compare))
    remaining = sum(damage)
    answer = 0
    for duration, rate, _ in jobs:
        answer += duration * remaining
        remaining -= rate
    return answer


class Solution:
    def minDamage(self, power: int, damage: list[int], health: list[int]) -> int:
        return solve(power, damage, health)
