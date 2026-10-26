"""3445. Maximum Difference Between Even and Odd Frequency II: eligible prefix minima indexed by two count parities."""


def solve(s: str, k: int) -> int:
    """O(25*n) time and O(5*n) auxiliary space. Inputs are preserved."""
    n = len(s)
    prefix = [[0] * (n + 1) for _ in range(5)]
    for digit in range(5):
        for index, character in enumerate(s):
            prefix[digit][index + 1] = prefix[digit][index] + (ord(character) - ord('0') == digit)
    answer = float('-inf')
    for first in range(5):
        for second in range(5):
            if first == second:
                continue
            a = prefix[first]
            b = prefix[second]
            minimum = [float('inf')] * 4
            left = 0
            for right in range(k, n + 1):
                while left <= right - k and b[right] - b[left] >= 2:
                    state = (a[left] % 2) * 2 + b[left] % 2
                    minimum[state] = min(minimum[state], a[left] - b[left])
                    left += 1
                state = ((a[right] % 2) ^ 1) * 2 + b[right] % 2
                answer = max(answer, a[right] - b[right] - minimum[state])
    return int(answer)


class Solution:
    def maxDifference(self, s: str, k: int) -> int:
        return solve(s, k)
