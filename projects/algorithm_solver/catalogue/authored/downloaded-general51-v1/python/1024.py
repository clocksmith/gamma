"""1024. Video Stitching (Medium).

Specification: https://leetcode.com/problems/video-stitching/description/
"""


def solve(clips: list[list[int]], time: int) -> int:
    ordered = sorted(clips)
    count = 0
    current_end = 0
    next_end = 0
    index = 0
    while current_end < time:
        while index < len(ordered) and ordered[index][0] <= current_end:
            next_end = max(next_end, ordered[index][1])
            index += 1
        if next_end <= current_end:
            return -1
        current_end = next_end
        count += 1
    return count


class Solution:
    def videoStitching(self, clips: list[list[int]], time: int) -> int:
        return solve(clips, time)
