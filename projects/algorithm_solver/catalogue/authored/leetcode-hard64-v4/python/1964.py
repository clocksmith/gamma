"""1964. Find the Longest Valid Obstacle Course at Each Position."""

from bisect import bisect_right


def solve(obstacles: list[int]) -> list[int]:
    """Upper-bound patience sorting for nondecreasing subsequences; O(n log n) time and O(n) space. Inputs are preserved."""
    tails = []
    answer = []
    for height in obstacles:
        position = bisect_right(tails, height)
        answer.append(position + 1)
        if position == len(tails):
            tails.append(height)
        else:
            tails[position] = height
    return answer


class Solution:
    def longestObstacleCourseAtEachPosition(self, obstacles: list[int]) -> list[int]:
        return solve(obstacles)
