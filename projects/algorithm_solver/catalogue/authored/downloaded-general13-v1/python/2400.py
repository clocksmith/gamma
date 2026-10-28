"""2400. Number of Ways to Reach a Position After Exactly k Steps (Medium).

Specification: https://leetcode.com/problems/number-of-ways-to-reach-a-position-after-exactly-k-steps/description/
"""


def solve(startPos, endPos, k):
    MOD = 1000000007
    cur = {abs(startPos - endPos): 1}
    for _ in range(k):
        nxt = {}
        for d, ways in cur.items():
            for nd in (d + 1, abs(d - 1)):
                nxt[nd] = (nxt.get(nd, 0) + ways) % MOD
        cur = nxt
    return cur.get(0, 0)


class Solution:
    def numberOfWays(self, startPos, endPos, k):
        return solve(startPos, endPos, k)
