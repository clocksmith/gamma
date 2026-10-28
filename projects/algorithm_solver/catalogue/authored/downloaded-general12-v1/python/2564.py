"""2564. Substring XOR Queries (Medium).

Specification: https://leetcode.com/problems/substring-xor-queries/description/
"""


def solve(s, queries):
    best = {}
    n = len(s)
    limit = 1 << 30
    for i in range(n):
        val = 0
        for j in range(i, min(n, i + 30)):
            val = val * 2 + int(s[j])
            if val >= limit:
                break
            length = j - i + 1
            cur = best.get(val)
            if cur is None or length < cur[2] or (length == cur[2] and i < cur[0]):
                best[val] = [i, j, length]
            if s[i] == '0':
                break
    ans = []
    for first, second in queries:
        hit = best.get(first ^ second)
        ans.append([hit[0], hit[1]] if hit is not None else [-1, -1])
    return ans


class Solution:
    def substringXorQueries(self, s, queries):
        return solve(s, queries)
