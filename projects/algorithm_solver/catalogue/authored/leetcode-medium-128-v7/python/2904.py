"""2904. Shortest and Lexicographically Smallest Beautiful String: compare minimal substrings spanning each consecutive group of k one positions."""


def solve(s: str, k: int) -> str:
    """O(n * n) worst-case time and O(n) auxiliary space; inputs are read-only."""
    positions = [index for index, character in enumerate(s) if character == '1']
    best = ''
    for index in range(len(positions) - k + 1):
        left, right = positions[index], positions[index + k - 1] + 1
        if best and right - left > len(best):
            continue
        candidate = s[left:right]
        if not best or len(candidate) < len(best) or candidate < best:
            best = candidate
    return best


class Solution:
    def shortestBeautifulSubstring(self, s: str, k: int) -> str:
        return solve(s, k)
