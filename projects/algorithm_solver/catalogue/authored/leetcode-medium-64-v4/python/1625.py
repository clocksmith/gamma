"""1625. Lexicographically Smallest String After Applying Operations: search the finite set of strings reachable by addition and rotation."""


def solve(s: str, a: int, b: int) -> str:
    """O(R * n) expected time and O(R * n) auxiliary space for R reachable strings; inputs are read-only."""
    seen = {s}
    stack = [s]
    best = s
    while stack:
        current = stack.pop()
        best = min(best, current)
        digits = list(current)
        for index in range(1, len(digits), 2):
            digits[index] = str((int(digits[index]) + a) % 10)
        added = ''.join(digits)
        rotated = current[-b:] + current[:-b]
        for following in (added, rotated):
            if following not in seen:
                seen.add(following)
                stack.append(following)
    return best


class Solution:
    def findLexSmallestString(self, s: str, a: int, b: int) -> str:
        return solve(s, a, b)
