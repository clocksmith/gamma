"""1349. Maximum Students Taking Exam: compatible row masks; O(rows*4^columns) time and O(2^columns) space."""


def solve(seats: list[list[str]]) -> int:
    columns = len(seats[0])
    previous = {0: 0}
    for row in seats:
        available = sum(1 << column for column in range(columns) if row[column] == '.')
        current = {}
        mask = available
        while True:
            if mask & (mask << 1) == 0:
                count = mask.bit_count()
                for before, value in previous.items():
                    if mask & (before << 1) == 0 and mask & (before >> 1) == 0:
                        current[mask] = max(current.get(mask, 0), value + count)
            if mask == 0:
                break
            mask = (mask - 1) & available
        previous = current
    return max(previous.values())


class Solution:
    def maxStudents(self, seats: list[list[str]]) -> int:
        return solve(seats)
