"""2182. Construct String With Repeat Limit: emit the largest available letter and use one smaller separator when needed."""


def solve(s: str, repeatLimit: int) -> str:
    """O(n) time and O(n) output-construction space for a fixed 26-letter alphabet; inputs are read-only."""
    counts = [0] * 26
    for character in s:
        counts[ord(character) - ord('a')] += 1
    pieces = []
    current = 25
    while current >= 0:
        if counts[current] == 0:
            current -= 1
            continue
        take = min(repeatLimit, counts[current])
        pieces.append(chr(ord('a') + current) * take)
        counts[current] -= take
        if counts[current] == 0:
            current -= 1
            continue
        separator = current - 1
        while separator >= 0 and counts[separator] == 0:
            separator -= 1
        if separator < 0:
            break
        pieces.append(chr(ord('a') + separator))
        counts[separator] -= 1
    return ''.join(pieces)


class Solution:
    def repeatLimitedString(self, s: str, repeatLimit: int) -> str:
        return solve(s, repeatLimit)
