"""1759. Count Number of Homogenous Substrings: add the length of the equal-character suffix at each position."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    previous = ''
    run = result = 0
    for letter in s:
        run = run + 1 if letter == previous else 1
        result = (result + run) % modulus
        previous = letter
    return result


class Solution:
    def countHomogenous(self, s: str) -> int:
        return solve(s)
