"""681. Next Closest Time."""

def solve(time: str) -> str:
    allowed = set(time.replace(':', ''))
    hours, minutes = map(int, time.split(':'))
    start = hours * 60 + minutes
    for elapsed in range(1, 1441):
        value = (start + elapsed) % 1440
        candidate = f'{value // 60:02d}:{value % 60:02d}'
        if all(char == ':' or char in allowed for char in candidate):
            return candidate
    return time


class Solution:
    def nextClosestTime(self, time: str) -> str:
        return solve(time)
