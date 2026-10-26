"""1353. Maximum Number of Events That Can Be Attended: attend the available event with the earliest ending day."""
from heapq import heappop, heappush


def solve(events: list[list[int]]) -> int:
    """O(n log(n + 1)) time and O(n) auxiliary space; inputs are read-only."""
    ordered = sorted(events)
    endings = []
    index = day = attended = 0
    while index < len(ordered) or endings:
        if not endings:
            day = ordered[index][0]
        while index < len(ordered) and ordered[index][0] <= day:
            heappush(endings, ordered[index][1])
            index += 1
        while endings and endings[0] < day:
            heappop(endings)
        if endings:
            heappop(endings)
            attended += 1
            day += 1
    return attended


class Solution:
    def maxEvents(self, events: list[list[int]]) -> int:
        return solve(events)
