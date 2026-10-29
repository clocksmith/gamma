"""Hack2Hire 67775b978df5ec401f786db0 (Ball Picking Game) over an INFERRED spec; qualification unknown."""


def solve(balls):
    n = len(balls)
    pre = [0] * (n + 1)
    for i, v in enumerate(balls):
        pre[i + 1] = pre[i] + v
    prev2 = [0] * (n + 1)  # diff for length L - 2, indexed by left end
    prev1 = [0] * (n + 1)  # diff for length L - 1
    for length in range(1, n + 1):
        cur = [0] * (n + 1)
        for l in range(n - length + 1):
            r = l + length  # interval balls[l:r]
            best = balls[l] - prev1[l + 1]
            x = balls[r - 1] - prev1[l]
            if x > best:
                best = x
            if length >= 2:
                x = balls[l] + balls[l + 1] - prev2[l + 2]
                if x > best:
                    best = x
                x = balls[r - 1] + balls[r - 2] - prev2[l]
                if x > best:
                    best = x
            cur[l] = best
        prev2, prev1 = prev1, cur
    diff = prev1[0] if n else 0
    return (pre[n] + diff) // 2


class Solution:
    def firstPlayerScore(self, balls):
        return solve(balls)
