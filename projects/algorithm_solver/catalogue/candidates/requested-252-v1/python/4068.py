"""4068. Maximize Meeting Earnings with Idle Gaps.

Specification: https://leetcode.com/problems/maximize-meeting-earnings-with-idle-gaps/description/
"""

from __future__ import annotations


def solve(meetings: list[list[int]]) -> int:
    """O(n log n) time and O(n) space; half-open meetings, idle revenue only between selected meetings. Inputs are preserved."""
    ordered = sorted(meetings, key=lambda meeting: meeting[1])
    best_minus_end = []
    answer = 0
    for index, (start, end, revenue) in enumerate(ordered):
        left, right = 0, index
        while left < right:
            middle = (left + right) // 2
            if ordered[middle][1] <= start:
                left = middle + 1
            else:
                right = middle
        ending = revenue + max(0, start + best_minus_end[left - 1] if left else float('-inf'))
        answer = max(answer, ending)
        best_minus_end.append(max(ending - end, best_minus_end[-1] if best_minus_end else float('-inf')))
    return answer
