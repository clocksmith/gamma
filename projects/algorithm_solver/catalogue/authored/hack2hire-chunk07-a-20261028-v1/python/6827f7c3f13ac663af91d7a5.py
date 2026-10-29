"""Hack2Hire 6827f7c3f13ac663af91d7a5 (Max Non-overlapping Tasks) over an INFERRED spec; qualification unknown."""

def solve(tasks):
    count, last_end = 0, None
    for start, end in sorted(tasks, key=lambda t: t[1]):
        if last_end is None or start >= last_end:
            count += 1
            last_end = end
    return count


class Solution:
    def maxNonOverlappingTasks(self, tasks):
        return solve(tasks)
