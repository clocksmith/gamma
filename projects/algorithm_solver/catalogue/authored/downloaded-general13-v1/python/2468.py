"""2468. Split Message Based on Limit (Hard).

Specification: https://leetcode.com/problems/split-message-based-on-limit/description/
"""


def solve(message, limit):
    n = len(message)
    sa = 0
    for k in range(1, n + 1):
        sa += len(str(k))
        sb = len(str(k)) * k
        sc = 3 * k
        if len(str(k)) * 2 + 3 >= limit:
            continue
        if limit * k - (sa + sb + sc) >= n:
            out = []
            idx = 0
            for part in range(1, k + 1):
                tag = f'<{part}/{k}>'
                cap = limit - len(tag)
                chunk = message[idx:idx + cap]
                idx += len(chunk)
                out.append(chunk + tag)
            return out
    return []


class Solution:
    def splitMessage(self, message, limit):
        return solve(message, limit)
