"""2337. Move Pieces to Obtain a String: match piece order while checking each piece can move only in its permitted direction."""


def solve(start: str, target: str) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    if len(start) != len(target):
        return False
    left = right = 0
    size = len(start)
    while True:
        while left < size and start[left] == '_':
            left += 1
        while right < size and target[right] == '_':
            right += 1
        if left == size or right == size:
            return left == size and right == size
        if start[left] != target[right]:
            return False
        if start[left] == 'L' and left < right:
            return False
        if start[left] == 'R' and left > right:
            return False
        left += 1
        right += 1


class Solution:
    def canChange(self, start: str, target: str) -> bool:
        return solve(start, target)
