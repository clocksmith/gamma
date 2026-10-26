"""2055. Plates Between Candles: combine plate prefixes with the closest enclosing candles."""


def solve(s: str, queries: list[list[int]]) -> list[int]:
    """O(n + q) time and O(n + q) auxiliary and result space; inputs are read-only."""
    size = len(s)
    prefix = [0] * (size + 1)
    left_candle = [-1] * size
    right_candle = [-1] * size
    last = -1
    for index, character in enumerate(s):
        prefix[index + 1] = prefix[index] + (character == '*')
        if character == '|':
            last = index
        left_candle[index] = last
    last = -1
    for index in range(size - 1, -1, -1):
        if s[index] == '|':
            last = index
        right_candle[index] = last
    result = []
    for left, right in queries:
        start, end = right_candle[left], left_candle[right]
        result.append(prefix[end] - prefix[start] if 0 <= start < end else 0)
    return result


class Solution:
    def platesBetweenCandles(self, s: str, queries: list[list[int]]) -> list[int]:
        return solve(s, queries)
