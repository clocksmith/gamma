"""1247. Minimum Swaps to Make Strings Equal: pair opposite mismatch types and handle the remaining pair."""


def solve(s1: str, s2: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    xy = yx = 0
    for first, second in zip(s1, s2):
        if first != second:
            if first == 'x':
                xy += 1
            else:
                yx += 1
    if (xy + yx) % 2:
        return -1
    return xy // 2 + yx // 2 + 2 * (xy % 2)


class Solution:
    def minimumSwap(self, s1: str, s2: str) -> int:
        return solve(s1, s2)
