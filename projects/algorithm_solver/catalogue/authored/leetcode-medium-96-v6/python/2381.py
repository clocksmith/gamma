"""2381. Shifting Letters II: accumulate signed interval shifts in a difference array."""


def solve(s: str, shifts: list[list[int]]) -> str:
    """O(n + q) time and O(n) auxiliary and result space; inputs are read-only."""
    difference = [0] * (len(s) + 1)
    for start, end, direction in shifts:
        amount = 1 if direction == 1 else -1
        difference[start] += amount
        difference[end + 1] -= amount
    current = 0
    result = []
    for index, character in enumerate(s):
        current += difference[index]
        letter = (ord(character) - ord('a') + current) % 26
        result.append(chr(ord('a') + letter))
    return ''.join(result)


class Solution:
    def shiftingLetters(self, s: str, shifts: list[list[int]]) -> str:
        return solve(s, shifts)
