"""2268. Minimum Number of Keypresses: assign the most frequent letters to the cheapest nine-key positions."""


def solve(s: str) -> int:
    """O(n + 26 log 26) time and O(26) auxiliary space; inputs are read-only."""
    counts = [0] * 26
    for char in s:
        counts[ord(char) - ord('a')] += 1
    counts.sort(reverse=True)
    return sum(count * (index // 9 + 1) for index, count in enumerate(counts))


class Solution:
    def minimumKeypresses(self, s: str) -> int:
        return solve(s)
