def sorted_endpoints(intervals: list[list[int]]) -> tuple[list[int], list[int]]:
    starts = sorted(interval[0] for interval in intervals)
    ends = sorted(interval[1] for interval in intervals)
    return starts, ends


class Solution:
    def canAttendMeetings(self, intervals: list[list[int]]) -> bool:
        starts, ends = sorted_endpoints(intervals)
        for index in range(1, len(starts)):
            # Touching half-open meetings do not overlap.
            if starts[index] < ends[index - 1]:
                return False
        return True
