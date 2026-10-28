"""781. Rabbits in Forest (Medium).

Specification: https://leetcode.com/problems/rabbits-in-forest/description/
"""


def solve(answers: list[int]) -> int:
    counts = {}
    for value in answers:
        counts[value] = counts.get(value, 0) + 1
    total = 0
    for answer, count in counts.items():
        group_size = answer + 1
        total += ((count + group_size - 1) // group_size) * group_size
    return total


class Solution:
    def numRabbits(self, answers: list[int]) -> int:
        return solve(answers)
