"""664. Strange Printer. Compress equal runs, then merge matching-character printing turns in interval DP."""

def solve(s: str) -> int:
    text = []
    for char in s:
        if not text or text[-1] != char:
            text.append(char)
    n = len(text)
    if not n:
        return 0
    dp = [[0] * n for _ in range(n)]
    for left in range(n - 1, -1, -1):
        dp[left][left] = 1
        for right in range(left + 1, n):
            best = 1 + dp[left + 1][right]
            for match in range(left + 1, right + 1):
                if text[match] == text[left]:
                    middle = dp[left + 1][match - 1] if match > left + 1 else 0
                    best = min(best, middle + dp[match][right])
            dp[left][right] = best
    return dp[0][-1]


class Solution:
    def strangePrinter(self, s: str) -> int:
        return solve(s)
