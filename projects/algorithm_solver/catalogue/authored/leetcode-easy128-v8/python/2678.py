"""2678. Number of Senior Citizens (Easy).

Specification: https://leetcode.com/problems/number-of-senior-citizens/description/
"""


def solve(details: list[str]) -> int:
    """O(n) time, O(1) auxiliary space; the two age digits occupy zero-based positions 11 and 12."""
    count = 0
    for detail in details:
        age = (ord(detail[11]) - 48) * 10 + ord(detail[12]) - 48
        if age > 60:
            count += 1
    return count


class Solution:
    def countSeniors(self, details: list[str]) -> int:
        return solve(details)
