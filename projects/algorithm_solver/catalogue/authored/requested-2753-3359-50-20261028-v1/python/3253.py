"""Original frontend 3253 variant; qualification unknown."""


def solve(target: str, words, costs) -> int:
    n = len(target)
    best = {}
    for w, c in zip(words, costs):
        if w not in best or c < best[w]:
            best[w] = c
    INF = 10**18
    dp = [INF] * (n + 1)
    dp[0] = 0
    for i in range(n):
        if dp[i] == INF:
            continue
        for w, c in best.items():
            L = len(w)
            if i + L <= n and target[i : i + L] == w:
                if dp[i] + c < dp[i + L]:
                    dp[i + L] = dp[i] + c
    return -1 if dp[n] == INF else dp[n]


minimumCost = solve


class Solution:
    def minimumCost(self, target: str, words, costs) -> int:
        return solve(target, words, costs)
