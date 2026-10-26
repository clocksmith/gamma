"""1700. Number of Students Unable to Eat Lunch (Easy).

Specification: https://leetcode.com/problems/number-of-students-unable-to-eat-lunch/description/
"""


def solve(students: list[int], sandwiches: list[int]) -> int:
    """O(n) time, O(1) space; count preferences instead of rotating the queue; preserve inputs."""
    remaining_by_type = [0, 0]
    for preference in students:
        remaining_by_type[preference] += 1
    remaining = len(students)
    for sandwich in sandwiches:
        if remaining_by_type[sandwich] == 0:
            break
        remaining_by_type[sandwich] -= 1
        remaining -= 1
    return remaining


class Solution:
    def countStudents(self, students: list[int], sandwiches: list[int]) -> int:
        return solve(students, sandwiches)
