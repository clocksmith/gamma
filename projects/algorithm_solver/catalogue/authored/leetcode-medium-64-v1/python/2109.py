"""2109. Adding Spaces to a String: join untouched source slices at the specified insertion positions."""


def solve(s: str, spaces: list[int]) -> str:
    """O(n + m) time and O(n + m) output-construction space; inputs are read-only."""
    pieces = []
    previous = 0
    for position in spaces:
        pieces.append(s[previous:position])
        previous = position
    pieces.append(s[previous:])
    return ' '.join(pieces)


class Solution:
    def addSpaces(self, s: str, spaces: list[int]) -> str:
        return solve(s, spaces)
