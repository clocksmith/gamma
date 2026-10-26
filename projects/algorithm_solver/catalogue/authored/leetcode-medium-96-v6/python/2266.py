"""2266. Count Number of Texts: count valid final key groups with a bounded dynamic-programming transition."""


def solve(pressedKeys: str) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    ways = [0] * (len(pressedKeys) + 1)
    ways[0] = 1
    for end in range(1, len(ways)):
        limit = 4 if pressedKeys[end - 1] in '79' else 3
        for length in range(1, limit + 1):
            if end < length or pressedKeys[end - length] != pressedKeys[end - 1]:
                break
            ways[end] = (ways[end] + ways[end - length]) % modulus
    return ways[-1]


class Solution:
    def countTexts(self, pressedKeys: str) -> int:
        return solve(pressedKeys)
