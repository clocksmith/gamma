"""2390. Removing Stars From a String: use a stack for the nearest surviving letter preceding each star."""


def solve(s: str) -> str:
    """O(n) time and O(n) auxiliary and result space; inputs are read-only."""
    letters = []
    for character in s:
        if character == '*':
            letters.pop()
        else:
            letters.append(character)
    return ''.join(letters)


class Solution:
    def removeStars(self, s: str) -> str:
        return solve(s)
