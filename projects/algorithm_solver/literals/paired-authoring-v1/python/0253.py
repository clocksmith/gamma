def sorted_endpoints(intervals: list[list[int]]) -> tuple[list[int], list[int]]:
    starts = sorted(interval[0] for interval in intervals)
    ends = sorted(interval[1] for interval in intervals)
    return starts, ends


class Solution:
    def minMeetingRooms(self, intervals: list[list[int]]) -> int:
        starts, ends = sorted_endpoints(intervals)
        end_index = 0
        active_rooms = 0
        peak_rooms = 0
        for start in starts:
            # Release all rooms whose meetings end at or before this start.
            while end_index < len(ends) and ends[end_index] <= start:
                active_rooms -= 1
                end_index += 1
            active_rooms += 1
            peak_rooms = max(peak_rooms, active_rooms)
        return peak_rooms
