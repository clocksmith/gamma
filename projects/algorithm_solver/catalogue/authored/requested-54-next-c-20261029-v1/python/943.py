def solve(words):
    n = len(words)
    overlap = [[0]*n for _ in range(n)]
    for i,a in enumerate(words):
        for j,b in enumerate(words):
            if i != j:
                overlap[i][j] = max((k for k in range(min(len(a),len(b))+1) if a.endswith(b[:k])),default=0)
    dp = [[None]*n for _ in range(1<<n)]
    for i,word in enumerate(words):
        dp[1<<i][i] = word
    for mask in range(1<<n):
        for last in range(n):
            current = dp[mask][last]
            if current is None:
                continue
            for nxt in range(n):
                if not mask & (1<<nxt):
                    candidate = current+words[nxt][overlap[last][nxt]:]
                    row = dp[mask | (1<<nxt)]
                    if row[nxt] is None or len(candidate) < len(row[nxt]):
                        row[nxt] = candidate
    return min((s for s in dp[-1] if s is not None),key=len)

class Solution:
    def shortestSuperstring(self, words):
        return solve(words)
