"""1947. Maximum Compatibility Score Sum: assign students in order using a subset of already chosen mentors."""


def solve(students: list[list[int]], mentors: list[list[int]]) -> int:
    """O(m^2 * q + m * 2^m) time and O(m^2 + 2^m) space, with m pairs and q questions; inputs are read-only."""
    count = len(students)
    scores = [[sum(left == right for left, right in zip(student, mentor))
               for mentor in mentors] for student in students]
    best = [-1] * (1 << count)
    best[0] = 0
    for mask in range((1 << count) - 1):
        student = mask.bit_count()
        for mentor in range(count):
            bit = 1 << mentor
            if mask & bit:
                continue
            next_mask = mask | bit
            best[next_mask] = max(best[next_mask], best[mask] + scores[student][mentor])
    return best[-1]


class Solution:
    def maxCompatibilitySum(self, students: list[list[int]], mentors: list[list[int]]) -> int:
        return solve(students, mentors)
