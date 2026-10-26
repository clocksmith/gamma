"""3386. Button with Longest Push Time (Easy).

Specification: https://leetcode.com/problems/button-with-longest-push-time/description/
"""


def solve(events: list[list[int]]) -> int:
    """O(n) time, O(1) auxiliary space; equal durations favor the smallest button index."""
    previous_time = 0
    longest = -1
    best_button = events[0][0]
    for button, time in events:
        duration = time - previous_time
        if duration > longest or (duration == longest and button < best_button):
            longest = duration
            best_button = button
        previous_time = time
    return best_button


class Solution:
    def buttonWithLongestTime(self, events: list[list[int]]) -> int:
        return solve(events)
