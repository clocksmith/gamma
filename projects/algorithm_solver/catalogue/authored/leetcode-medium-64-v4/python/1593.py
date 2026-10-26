"""1593. Split a String Into the Max Number of Unique Substrings: backtrack over distinct pieces and prune by the remaining character budget."""


def solve(s: str) -> int:
    """O(n * 2^n) time and O(n^2) auxiliary space including retained substring text; inputs are read-only."""
    used = set()
    best = 0

    def visit(start: int) -> None:
        nonlocal best
        if len(used) + len(s) - start <= best:
            return
        if start == len(s):
            best = len(used)
            return
        for end in range(start + 1, len(s) + 1):
            word = s[start:end]
            if word in used:
                continue
            used.add(word)
            visit(end)
            used.remove(word)

    visit(0)
    return best


class Solution:
    def maxUniqueSplit(self, s: str) -> int:
        return solve(s)
