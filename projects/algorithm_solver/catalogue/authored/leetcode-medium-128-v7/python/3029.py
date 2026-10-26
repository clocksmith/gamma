"""3029. Minimum Time to Revert Word to Initial State I: find the first allowed removal length leaving a suffix equal to the initial prefix."""


def solve(word: str, k: int) -> int:
    """O(n * n) worst-case time and O(n) auxiliary space; inputs are read-only."""
    removed = k
    while removed < len(word):
        if word.startswith(word[removed:]):
            return removed // k
        removed += k
    return (len(word) + k - 1) // k


class Solution:
    def minimumTimeToInitialState(self, word: str, k: int) -> int:
        return solve(word, k)
