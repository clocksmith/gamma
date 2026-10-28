"""1931. Painting a Grid With Three Different Colors (Hard).

Specification: https://leetcode.com/problems/painting-a-grid-with-three-different-colors/description/
"""

MOD = 1000000007


def solve(m: int, n: int) -> int:
    states = []

    def build(state):
        if len(state) == m:
            states.append(tuple(state))
            return
        for c in range(3):
            if not state or state[-1] != c:
                state.append(c)
                build(state)
                state.pop()

    build([])

    def compatible(a, b):
        return all(x != y for x, y in zip(a, b))

    dp = [1] * len(states)
    for _ in range(1, n):
        nxt = [0] * len(states)
        for j in range(len(states)):
            for k in range(len(states)):
                if compatible(states[j], states[k]):
                    nxt[k] = (nxt[k] + dp[j]) % MOD
        dp = nxt
    return sum(dp) % MOD


class Solution:
    def colorTheGrid(self, m: int, n: int) -> int:
        return solve(m, n)
