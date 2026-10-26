"""2402. Meeting Rooms III. Separate heaps for available rooms and their finishing times."""

from heapq import heappop, heappush


def solve(n: int, meetings: list[list[int]]) -> int:
    """O(m log m+(m+n) log(n+1)) time and O(m+n) space. Inputs are preserved."""
    available = list(range(n))
    busy = []
    counts = [0] * n
    for start, end in sorted(meetings):
        while busy and busy[0][0] <= start:
            _, room = heappop(busy)
            heappush(available, room)
        if available:
            room = heappop(available)
            finish = end
        else:
            free_at, room = heappop(busy)
            finish = free_at + end - start
        counts[room] += 1
        heappush(busy, (finish, room))
    return max(range(n), key=lambda room: (counts[room], -room))


class Solution:
    def mostBooked(self, n: int, meetings: list[list[int]]) -> int:
        return solve(n, meetings)
