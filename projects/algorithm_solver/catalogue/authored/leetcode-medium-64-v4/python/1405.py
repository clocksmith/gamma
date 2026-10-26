"""1405. Longest Happy String: take the most frequent available letter unless it would create three equal neighbors."""


def solve(a: int, b: int, c: int) -> str:
    """O(a + b + c) time and O(a + b + c) space including the output; inputs are read-only."""
    counts = [[a, 'a'], [b, 'b'], [c, 'c']]
    result = []
    while True:
        counts.sort(key=lambda item: (-item[0], item[1]))
        selected = 0
        if len(result) >= 2 and result[-1] == result[-2] == counts[0][1]:
            selected = 1
        if counts[selected][0] == 0:
            break
        result.append(counts[selected][1])
        counts[selected][0] -= 1
    return ''.join(result)


class Solution:
    def longestDiverseString(self, a: int, b: int, c: int) -> str:
        return solve(a, b, c)
