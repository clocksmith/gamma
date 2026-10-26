"""2575. Find the Divisibility Array of a String: carry only the decimal prefix remainder rather than constructing huge integers."""


def solve(word: str, m: int) -> list[int]:
    """O(n) time and O(n) auxiliary space including the result; inputs are read-only."""
    remainder = 0
    result = []
    for character in word:
        remainder = (remainder * 10 + ord(character) - ord('0')) % m
        result.append(int(remainder == 0))
    return result


class Solution:
    def divisibilityArray(self, word: str, m: int) -> list[int]:
        return solve(word, m)
