"""2125. Number of Laser Beams in a Bank: multiply device counts in consecutive nonempty rows."""


def solve(bank: list[str]) -> int:
    """O(rows * columns) time and O(1) auxiliary space; inputs are read-only."""
    previous = answer = 0
    for row in bank:
        devices = row.count('1')
        if devices:
            answer += previous * devices
            previous = devices
    return answer


class Solution:
    def numberOfBeams(self, bank: list[str]) -> int:
        return solve(bank)
