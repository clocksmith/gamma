"""1540. Can Convert String in K Moves: assign each repeated shift its next available move."""


def solve(s: str, t: str, k: int) -> bool:
    """O(n) time and O(1) auxiliary space for lowercase English letters; inputs are read-only."""
    if len(s) != len(t):
        return False
    counts = [0] * 26
    for source, target in zip(s, t):
        shift = (ord(target) - ord(source)) % 26
        if shift == 0:
            continue
        move = shift + 26 * counts[shift]
        if move > k:
            return False
        counts[shift] += 1
    return True


class Solution:
    def canConvertString(self, s: str, t: str, k: int) -> bool:
        return solve(s, t, k)
