"""2976. Minimum Cost to Convert String I: compute all-pairs character conversion costs before summing corresponding positions."""


def solve(source: str, target: str, original: list[str], changed: list[str], cost: list[int]) -> int:
    """O(26^3 + n + e) time and O(26^2) auxiliary space; inputs are read-only."""
    distance = [[float('inf')] * 26 for _ in range(26)]
    for code in range(26):
        distance[code][code] = 0
    for before, after, price in zip(original, changed, cost):
        left = ord(before) - ord('a')
        right = ord(after) - ord('a')
        distance[left][right] = min(distance[left][right], price)
    for middle in range(26):
        for left in range(26):
            if distance[left][middle] == float('inf'):
                continue
            for right in range(26):
                distance[left][right] = min(distance[left][right], distance[left][middle] + distance[middle][right])
    total = 0
    for before, after in zip(source, target):
        price = distance[ord(before) - ord('a')][ord(after) - ord('a')]
        if price == float('inf'):
            return -1
        total += price
    return total


class Solution:
    def minimumCost(self, source: str, target: str, original: list[str], changed: list[str], cost: list[int]) -> int:
        return solve(source, target, original, changed, cost)
