"""551. Student Attendance Record I (Easy).

Specification: https://leetcode.com/problems/student-attendance-record-i/description/
"""


def solve(s: str) -> bool:
    """O(n) time, O(1) space; reject two absences or three consecutive late days."""
    absences = 0
    late_run = 0
    for character in s:
        if character == 'A':
            absences += 1
        late_run = late_run + 1 if character == 'L' else 0
        if absences >= 2 or late_run >= 3:
            return False
    return True


class Solution:
    def checkRecord(self, s: str) -> bool:
        return solve(s)
