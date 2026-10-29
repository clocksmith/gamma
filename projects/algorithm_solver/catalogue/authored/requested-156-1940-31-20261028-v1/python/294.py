"""Original frontend 294 variant; qualification unknown."""


def solve(currentState: str) -> bool:
    runs = []
    cur = 0
    for ch in currentState:
        if ch == "+":
            cur += 1
        else:
            if cur >= 2:
                runs.append(cur)
            cur = 0
    if cur >= 2:
        runs.append(cur)
    if not runs:
        return False
    mx = max(runs)
    g = [0] * (mx + 1)
    for L in range(2, mx + 1):
        seen = {g[i] ^ g[L - 2 - i] for i in range((L - 1) // 2 + 1)}
        mex = 0
        while mex in seen:
            mex += 1
        g[L] = mex
    xor_sum = 0
    for r in runs:
        xor_sum ^= g[r]
    return xor_sum != 0


canWin = solve


class Solution:
    def canWin(self, currentState: str) -> bool:
        return solve(currentState)
